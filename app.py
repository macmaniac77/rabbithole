from flask import Flask, request, jsonify, render_template, abort, g 
import os
from pathlib import Path
from openai import OpenAI # Will be replaced by Gemini
import google.generativeai as genai # Added Google Gemini
from markupsafe import Markup
import markdown2
import re
import html
import json 
from typing import Dict, Optional, List, Literal 
from datetime import datetime, timedelta, timezone
import uuid
import jwt 
from functools import wraps

# --- Stripe Integration ---
import stripe 

# --- Lightning (LNbits) Integration ---
import hashlib 
import hmac    

# --- Model Imports ---
from models import UserContext as PydanticUserContext 

# --- LLM Strategy Imports ---
from llm_strategies import get_prompt_for_bigger, get_prompts_for_deeper 

# --- GitOps Integration ---
from git_ops import prepare_commit_message, commit_and_push 
from git_ops import ensure_git_repo as initialize_git_repo_at_startup

# --- Database Integration ---
from sqlalchemy.orm import Session
from database import (
    SessionLocal, 
    engine, 
    create_db_and_tables, 
    DBUserContext, 
    DBValuePoint,
    DBAuthUser
)

# --- Bcrypt Initialization ---
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app) 

create_db_and_tables() 
initialize_git_repo_at_startup() 

# --- Google Gemini Configuration ---
try:
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("Warning: GOOGLE_API_KEY environment variable not set. LLM calls will fail.")
    else:
        genai.configure(api_key=google_api_key)
except Exception as e:
    print(f"Error configuring Google API key for genai: {e}")

BASE_DIR = Path("RABBITHOLE/markdown") 

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-default-secret-key-please-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str):
    try: return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError: return "Token expired"
    except jwt.InvalidTokenError: return "Invalid token"
    except Exception as e: print(f"Token error: {e}"); return "Token error"

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "): return jsonify({"message": "Auth header missing/invalid"}), 401
        token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None
        if not token: return jsonify({"message": "Token missing"}), 401
        payload = decode_access_token(token)
        if isinstance(payload, str): return jsonify({"message": payload}), 401
        g.current_user_id = payload.get("sub")
        if not g.current_user_id: return jsonify({"message": "Token missing user identifier"}), 401
        return f(*args, **kwargs)
    return decorated

def get_db_session() -> Session: return SessionLocal()

def get_or_create_user_context(user_id: str, db: Session) -> DBUserContext:
    user_ctx = db.query(DBUserContext).filter(DBUserContext.user_id == user_id).first()
    if not user_ctx:
        user_ctx = DBUserContext(user_id=user_id, infra={}) 
        db.add(user_ctx)
        db.commit(); db.refresh(user_ctx)
    return user_ctx

def serialize_user_context_for_git(user_context_db: DBUserContext) -> Dict:
    try:
        pydantic_data = PydanticUserContext(
            user_id=user_context_db.user_id,
            active_vps=[vp.id for vp in user_context_db.active_vps_rels],
            completed_vps=[vp.id for vp in user_context_db.completed_vps_rels],
            credits_usd=user_context_db.credits_usd,
            credits_sat=user_context_db.credits_sat,
            last_input=user_context_db.last_input,
            infra=user_context_db.infra
        )
        return pydantic_data.model_dump(mode='json')
    except Exception as e: 
        print(f"PydanticUserContext processing failed ({e}), falling back to manual dict construction.")
        return {
            "user_id": user_context_db.user_id,
            "active_vps": [vp.id for vp in user_context_db.active_vps_rels],
            "completed_vps": [vp.id for vp in user_context_db.completed_vps_rels],
            "credits_usd": user_context_db.credits_usd,
            "credits_sat": user_context_db.credits_sat,
            "last_input": user_context_db.last_input,
            "infra": user_context_db.infra,
        }

def create_vp(db: Session, user_id: str, title: str, vp_type: Literal["payment", "contract", "task", "earn", "settle"], interface: str, price_usd: Optional[float] = None, price_sat: Optional[int] = None, expires: Optional[datetime] = None, creditable: bool = True, btc_commit: bool = False, next_vps: List[str] = []) -> DBValuePoint:
    vp_id = str(uuid.uuid4())
    user_context = get_or_create_user_context(user_id, db) 
    new_vp = DBValuePoint(id=vp_id, title=title, vp_type=vp_type, price_usd=price_usd, price_sat=price_sat, expires=expires, interface=interface, creditable=creditable, btc_commit=btc_commit, next=next_vps)
    db.add(new_vp)
    if new_vp not in user_context.active_vps_rels: user_context.active_vps_rels.append(new_vp)
    return new_vp

def spawn_child_vps(db: Session, parent_vp: DBValuePoint, user_id: str):
    newly_spawned_vps = []
    if parent_vp.vp_type == "contract" and parent_vp.title == "Basic Content Creation Contract":
        task1 = create_vp(db,user_id,"Draft Article","task","ui_interfaces/task_fulfill_order.md")
        task2 = create_vp(db,user_id,"Review Article","task","ui_interfaces/task_fulfill_order.md")
        newly_spawned_vps.extend([task1, task2])
    elif parent_vp.vp_type == "payment" and parent_vp.price_usd is not None and parent_vp.price_usd > 10.0:
        newly_spawned_vps.append(create_vp(db,user_id,f"Fulfill Order","task","ui_interfaces/task_fulfill_order.md"))
    if newly_spawned_vps:
        parent_vp.next = parent_vp.next + [vp.id for vp in newly_spawned_vps if vp.id not in parent_vp.next]
        db.add(parent_vp)

def get_folder_structure(base_path):
    structure = [] ; folders = [] ; files = []
    for entry in os.scandir(base_path):
        if entry.is_dir(): folders.append({'type': 'folder', 'name': entry.name, 'children': get_folder_structure(entry.path)})
        elif entry.is_file() and entry.name.endswith('.md'): files.append({'type': 'file', 'name': entry.name, 'path': os.path.relpath(entry.path, BASE_DIR).replace('\\', '/')})
    folders.sort(key=lambda x: x['name'].lower()); files.sort(key=lambda x: x['name'].lower())
    structure.extend(folders); structure.extend(files)
    return structure

def read_document(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f: return f.read()

def write_document(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True) 
    with open(path, 'w', encoding='utf-8') as f: f.write(content)

def sanitize_filename(name: str) -> str:
    name = re.sub(r'\s+', '_', name) 
    return re.sub(r'[<>:"/\\|?*]', '', name)[:50]

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(); username = data.get('username'); password = data.get('password')
    if not username or not password: return jsonify({"message": "Username/password required"}), 400
    db = get_db_session()
    try:
        if db.query(DBAuthUser).filter_by(username=username).first(): return jsonify({"message": "User exists"}), 400
        new_user = DBAuthUser(username=username); new_user.set_password(password)
        db.add(new_user); get_or_create_user_context(username, db); db.commit()
        return jsonify({"message": "User registered"}), 201
    finally: db.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(); username = data.get('username'); password = data.get('password')
    if not username or not password: return jsonify({"message": "Username/password required"}), 400
    db = get_db_session()
    try:
        user = db.query(DBAuthUser).filter_by(username=username).first()
        if user and user.check_password(password):
            return jsonify(access_token=create_access_token(data={"sub": username})), 200
        return jsonify({"message": "Invalid credentials"}), 401
    finally: db.close()

@app.route('/')
def index():
    db = get_db_session()
    try:
        user_id = getattr(g, 'current_user_id', "test_user_for_index_view")
        user_ctx = get_or_create_user_context(user_id, db)
        if not user_ctx.active_vps_rels and not user_ctx.completed_vps_rels and user_id == "test_user_for_index_view":
            create_vp(db, user_id, "Welcome Task", "task", "ui_interfaces/welcome_task.md")
            db.commit() 
        return render_template('index.html', structure=get_folder_structure(BASE_DIR), user_context=serialize_user_context_for_git(user_ctx), active_vps=list(user_ctx.active_vps_rels))
    finally: db.close()

@app.route('/view_document/<path:doc_path>')
def view_document(doc_path_str: str):
    full_path = BASE_DIR / doc_path_str
    if not full_path.is_file(): abort(404)
    return jsonify({"html_content": markdown2.markdown(read_document(full_path)), "markdown_content": read_document(full_path)})

@app.route('/edit_document', methods=['POST'])
@jwt_required
def edit_document():
    user_id = g.current_user_id; data = request.json
    doc_path = data.get('doc_path'); content = data.get('content')
    if not doc_path or content is None: return jsonify({"message":"doc_path and content required"}), 400
    write_document(BASE_DIR / doc_path, content)
    db = get_db_session()
    try:
        user_ctx = get_or_create_user_context(user_id, db); user_ctx.last_input = f"Edited: {doc_path}"; db.commit()
        commit_and_push(user_id, serialize_user_context_for_git(user_ctx), prepare_commit_message(user_id, "edited by user", doc_path=doc_path), source_markdown_relative_paths_to_copy=[doc_path])
        return jsonify({"message": "Document updated"})
    finally: db.close()

@app.route('/generate_document', methods=['POST'])
@jwt_required
def generate_document_route(): 
    user_id = g.current_user_id; data = request.json
    doc_path = data.get('doc_path'); operation = data.get('operation', 'alter'); context_text = data.get('context_text')
    if not context_text: return jsonify({"message":"context_text required"}), 400
    
    db = get_db_session()
    user_context_dict_for_git = {}
    try:
        user_ctx = get_or_create_user_context(user_id, db); user_ctx.last_input = context_text; db.commit()
        user_prompt_info = f"User ID: {user_id}\nCredits USD: {user_ctx.credits_usd}\n"
        user_context_dict_for_git = serialize_user_context_for_git(user_ctx) 
    finally: db.close()

    current_doc_full_path = BASE_DIR / doc_path if doc_path else None
    prompt_for_llm = ""
    if operation == 'alter' and current_doc_full_path and current_doc_full_path.is_file():
        prompt_for_llm = f"{user_prompt_info}Alter content:\n\n{read_document(current_doc_full_path)}\n\nInstructions:\n{context_text}"
    else:
        operation = 'generate'; prompt_for_llm = f"{user_prompt_info}Generate new document from context:\n\n{context_text}"
    
    try:
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = gemini_model.generate_content(prompt_for_llm)
        new_llm_content = response.text.strip()
    except Exception as e_llm:
        print(f"Error calling Google LLM for document generation: {e_llm}")
        return jsonify({"message": f"LLM Error: {str(e_llm)}"}), 500
    
    final_doc_path_rel = ""
    if operation == 'generate':
        try:
            title_prompt = f"Create a concise, filename-friendly title (max 5 words, no special characters other than underscore) for the following text:\n\n{new_llm_content[:200]}"
            title_response = gemini_model.generate_content(title_prompt)
            title = sanitize_filename(title_response.text.strip().replace('"', ''))
        except Exception as e_title:
            print(f"Error generating title with LLM: {e_title}")
            title = sanitize_filename(context_text[:30]) 
            
        file_name = title + ".md"
        parent_dir = (BASE_DIR / doc_path).parent if doc_path and current_doc_full_path and current_doc_full_path.is_file() else BASE_DIR 
        new_doc_full_path = parent_dir / file_name
        write_document(new_doc_full_path, new_llm_content)
        final_doc_path_rel = str(new_doc_full_path.relative_to(BASE_DIR))
        message = f"Document '{file_name}' generated."
    else: 
        write_document(current_doc_full_path, new_llm_content)
        final_doc_path_rel = doc_path
        message = "Document updated."
        
    commit_and_push(user_id, user_context_dict_for_git, prepare_commit_message(user_id, f"{operation} LLM", doc_path=final_doc_path_rel), source_markdown_relative_paths_to_copy=[final_doc_path_rel])
    return jsonify({"message": message, "content": new_llm_content, "doc_path": final_doc_path_rel})

@app.route('/webhook/stripe', methods=['POST'])
def webhook_stripe():
    stripe.api_key = os.getenv("STRIPE_API_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret: return jsonify({"error": "Stripe webhook secret not set"}), 500
    payload = request.data; sig_header = request.headers.get('Stripe-Signature')
    try: event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e: return jsonify({"error": str(e)}), 400

    db = get_db_session()
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            doc_id_rel_str = metadata.get('document_id') 
            action_type = metadata.get('action_type')
            is_public_contribution_str = metadata.get('is_public_contribution', 'false').lower()
            is_public_contribution = is_public_contribution_str == 'true'
            
            raw_path_history = metadata.get('document_path_history') 
            document_path_history_list = []
            if raw_path_history:
                try:
                    loaded_history = json.loads(raw_path_history)
                    if isinstance(loaded_history, list):
                        document_path_history_list = [str(item) for item in loaded_history]
                        print(f"Received document_path_history: {document_path_history_list}")
                    else: print(f"Warning: document_path_history from Stripe metadata was not a list: {raw_path_history}")
                except json.JSONDecodeError: print(f"Warning: Failed to parse document_path_history JSON from Stripe: {raw_path_history}")

            client_user_id = session.get('client_reference_id')
            user_context_db_instance = None
            payment_vp_instance = None
            actor_id_for_git = f"public_anon_{session.get('id', uuid.uuid4().hex[:8])[:8]}"
            auth_user = None
            if client_user_id: auth_user = db.query(DBAuthUser).filter(DBAuthUser.username == client_user_id).first()

            if auth_user: 
                actor_id_for_git = client_user_id
                user_context_db_instance = get_or_create_user_context(client_user_id, db)
                if session.get('currency') == 'usd': user_context_db_instance.credits_usd += float(session.get('amount_total', 0) / 100.0)
                payment_vp_title = f"Stripe Payment: {session.get('amount_total',0)/100.0} {session.get('currency','').upper()}"
                payment_vp_instance = create_vp(db, client_user_id, payment_vp_title, "payment", "ui_interfaces/payment_receipt.md", price_usd=float(session.get('amount_total',0)/100.0))
                if not is_public_contribution: spawn_child_vps(db, payment_vp_instance, client_user_id)
            elif is_public_contribution:
                actor_id_for_git = f"public_contrib_{session.get('id', uuid.uuid4().hex[:8])[:8]}"
            elif client_user_id: 
                actor_id_for_git = client_user_id 
                user_context_db_instance = get_or_create_user_context(client_user_id, db)
                if session.get('currency') == 'usd': user_context_db_instance.credits_usd += float(session.get('amount_total', 0) / 100.0)
                payment_vp_title = f"Stripe Payment (Guest): {session.get('amount_total',0)/100.0} {session.get('currency','').upper()}"
                payment_vp_instance = create_vp(db, client_user_id, payment_vp_title, "payment", "ui_interfaces/payment_receipt.md", price_usd=float(session.get('amount_total',0)/100.0))
                if not is_public_contribution: spawn_child_vps(db, payment_vp_instance, client_user_id)
            
            llm_action_taken = False
            files_for_overall_git_commit = [] 
            llm_action_description_for_commit = ""
            path_history_summary_for_llm = None

            if document_path_history_list:
                titles_in_path = [Path(p).name for p in document_path_history_list]
                path_titles_str = " -> ".join(titles_in_path)
                summary_parts = [f"User reached current doc ('{Path(doc_id_rel_str).name if doc_id_rel_str else 'N/A'}') via: '{path_titles_str}'."]
                if document_path_history_list: # If history is not empty
                    prev_doc_rel_path = document_path_history_list[-1]
                    prev_doc_full_path = BASE_DIR / prev_doc_rel_path
                    if prev_doc_full_path.is_file():
                        try:
                            prev_content = read_document(prev_doc_full_path)
                            excerpt = prev_content[:500].strip() + ("..." if len(prev_content) > 500 else "")
                            summary_parts.append(f"Excerpt from preceding doc ('{Path(prev_doc_rel_path).name}'):\n{excerpt}")
                        except Exception as e_read: print(f"Error reading hist doc {prev_doc_rel_path}: {e_read}")
                path_history_summary_for_llm = "\n".join(summary_parts)

            if doc_id_rel_str and action_type:
                target_doc_full_path = BASE_DIR / doc_id_rel_str
                if not target_doc_full_path.is_file():
                    print(f"Error: Document for '{action_type}' action not found: {target_doc_full_path}")
                else:
                    try:
                        original_content = read_document(target_doc_full_path)
                        prompt_user_info = f"User ID: {actor_id_for_git}\n"
                        if user_context_db_instance: prompt_user_info = f"User ID: {user_context_db_instance.user_id}\nCredits USD: {user_context_db_instance.credits_usd}\n"
                        
                        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')

                        if action_type == "bigger":
                            prompt = get_prompt_for_bigger(original_content, doc_id_rel_str, path_history_summary_for_llm)
                            response = gemini_model.generate_content(user_prompt_info + prompt)
                            llm_response = response.text.strip()
                            if llm_response:
                                write_document(target_doc_full_path, llm_response)
                                files_for_overall_git_commit.append(doc_id_rel_str)
                                llm_action_taken = True; llm_action_description_for_commit = f"LLM 'bigger' on {Path(doc_id_rel_str).name}"
                        elif action_type == "deeper":
                            prompt = get_prompts_for_deeper(original_content, doc_id_rel_str, path_history_summary_for_llm)
                            generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
                            response = gemini_model.generate_content(user_prompt_info + prompt, generation_config=generation_config)
                            llm_json_response_str = response.text.strip()
                            try:
                                llm_data = json.loads(llm_json_response_str)
                                new_title = llm_data.get("new_doc_title", "Untitled"); new_content = llm_data.get("new_doc_content", "")
                                link_phrase = llm_data.get("link_phrase_in_original_doc")
                                new_filename = sanitize_filename(new_title) + ".md"
                                new_doc_dir = target_doc_full_path.parent / "deeper_links"; new_doc_dir.mkdir(exist_ok=True)
                                new_doc_full_path_deeper = new_doc_dir / new_filename
                                write_document(new_doc_full_path_for_deeper, new_doc_content)
                                files_for_overall_git_commit.append(str(new_doc_full_path_for_deeper.relative_to(BASE_DIR)))
                                if link_phrase and link_phrase in original_content:
                                    link_to_new = os.path.join("deeper_links", new_filename)
                                    original_content = original_content.replace(link_phrase, f"{link_phrase} ([{new_title}](./{link_to_new}))", 1)
                                    write_document(target_doc_full_path, original_content)
                                if doc_id_rel_str not in files_for_overall_git_commit: files_for_overall_git_commit.append(doc_id_rel_str)
                                llm_action_taken = True; llm_action_description_for_commit = f"LLM 'deeper' on {Path(doc_id_rel_str).name}, new: {new_filename}"
                            except json.JSONDecodeError as e: print(f"LLM 'deeper' JSON error: {e}. Raw: {llm_json_response_str}")
                    except Exception as e_llm: print(f"Error during LLM for {doc_id_rel_str}: {e_llm}")
            
            db.commit() 
            
            user_context_data_for_git = {}
            git_json_user_id_filename = actor_id_for_git 
            
            if user_context_db_instance: 
                user_context_data_for_git = serialize_user_context_for_git(user_context_db_instance)
                git_json_user_id_filename = user_context_db_instance.user_id
            elif is_public_contribution : 
                 user_context_data_for_git = {"note": f"Public contribution by {actor_id_for_git}", "details": {"stripe_session": session.get('id'), "llm_action": action_type, "doc_id": doc_id_rel_str, "history": document_path_history_list}, "timestamp": datetime.now(timezone.utc).isoformat()}
            
            final_commit_action_desc = "payment_processed"
            if payment_vp_instance: final_commit_action_desc = f"payment_vp_{payment_vp_instance.id}"
            if llm_action_taken: final_commit_action_desc += f"_{llm_action_description_for_commit.replace(' ', '_').lower()}"
            
            final_commit_msg = prepare_commit_message(user_id=actor_id_for_git, vp_id=payment_vp_instance.id if payment_vp_instance else None, action=final_commit_action_desc)
            
            commit_and_push(
                user_id=git_json_user_id_filename, 
                user_context_data=user_context_data_for_git,
                commit_message=final_commit_msg, 
                source_markdown_relative_paths_to_copy=files_for_overall_git_commit if files_for_overall_git_commit else None
            )
        else: print(f"Unhandled Stripe event type: {event['type']}")
        return jsonify({"status":"success"}), 200
    except Exception as e:
        db.rollback(); print(f"Error in Stripe webhook: {e}"); import traceback; traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
    finally: db.close()

@app.route('/webhook/lightning', methods=['POST'])
def webhook_lightning(): 
    lnbits_webhook_secret = os.getenv("LNBITS_WEBHOOK_SECRET")
    payload = request.data 
    if lnbits_webhook_secret:
        received_signature = request.headers.get('X-LNBITS-Signature') 
        if not received_signature: return jsonify({"error": "Missing signature"}), 400
        computed_signature = hmac.new(key=lnbits_webhook_secret.encode('utf-8'), msg=payload, digestmod=hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed_signature, received_signature): return jsonify({"error": "Invalid signature"}), 400
    data = request.json 
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400
    db = get_db_session()
    try:
        user_id = data.get('memo') 
        payment_hash = data.get('payment_hash')
        if not user_id and 'extradata' in data and isinstance(data['extradata'], dict): user_id = data['extradata'].get('user_id')
        if not user_id: return jsonify({"error": "user_id not found in webhook payload"}), 400
        user_context_db = get_or_create_user_context(user_id, db) 
        amount_msat = data.get('amount'); 
        if amount_msat is None: amount_msat = data.get('amount_msat', 0)
        amount_sat = int(amount_msat / 1000)
        user_context_db.credits_sat += amount_sat
        payment_vp = create_vp(db=db, user_id=user_id, title=f"Lightning Payment: {amount_sat} sats (Hash: {payment_hash[:8] if payment_hash else 'N/A'}...)", vp_type="payment", interface="ui_interfaces/payment_receipt.md", price_sat=amount_sat) 
        spawn_child_vps(db, payment_vp, user_id)
        db.commit()
        user_context_dict = serialize_user_context_for_git(user_context_db)
        commit_msg = prepare_commit_message(user_id=user_id, vp_id=payment_vp.id, action="payment_received_lightning")
        commit_and_push(user_id=user_id, user_context_data=user_context_dict, commit_message=commit_msg)
        return jsonify({"status": "success", "payment_hash": payment_hash}), 200
    except Exception as e:
        db.rollback(); print(f"Error processing Lightning webhook: {e}"); import traceback; traceback.print_exc()
        return jsonify({"error": "Internal server error during Lightning webhook processing"}), 500
    finally: db.close()

@app.route('/vp/complete', methods=['POST'])
@jwt_required 
def vp_complete():
    user_id = g.current_user_id 
    vp_id = request.json.get('vp_id')
    if not vp_id: return jsonify({"message": "vp_id is required"}), 400
    db: Session = get_db_session()
    try:
        user_context_db = get_or_create_user_context(user_id, db)
        completed_vp = db.query(DBValuePoint).filter(DBValuePoint.id == vp_id).first()
        if not completed_vp: return jsonify({"error": "ValuePoint not found"}), 404
        if completed_vp not in user_context_db.active_vps_rels: return jsonify({"error": "ValuePoint not active for this user"}), 404
        user_context_db.active_vps_rels.remove(completed_vp)
        if completed_vp not in user_context_db.completed_vps_rels: user_context_db.completed_vps_rels.append(completed_vp)
        spawn_child_vps(db=db, parent_vp=completed_vp, user_id=user_id)
        db.commit() 
        user_context_dict = serialize_user_context_for_git(user_context_db)
        commit_msg = prepare_commit_message(user_id=user_id, vp_id=vp_id, action="completed_and_spawned_children")
        commit_and_push(user_id=user_id, user_context_data=user_context_dict, commit_message=commit_msg)
        return jsonify({"message": f"ValuePoint {vp_id} marked as complete.", "completed_vp_id": vp_id}), 200
    finally:
        db.close()

def render_folders(structure):
    html = '<ul>' 
    for item in structure:
        if item['type'] == 'folder':
            html += f'<li class="folder-item"><div class="folder-header" onclick="toggleFolder(this)"><i class="fas fa-chevron-right folder-icon"></i><span class="folder-name">{item["name"]}</span></div><div class="folder-content">{render_folders(item["children"])}</div></li>'
        elif item['type'] == 'file':
            html += f'<li class="file-item" id="file-{item["path"].replace("/", "-")}" onclick="loadMarkdown(\'{item["path"]}\', event)"><i class="fas fa-file file-icon"></i><span class="file-name">{item["name"]}</span></li>'
    html += '</ul>'
    return Markup(html)

app.jinja_env.globals.update(render_folders=render_folders)

if __name__ == '__main__':
    app.run(debug=True)
