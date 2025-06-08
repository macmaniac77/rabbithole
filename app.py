from flask import Flask, request, jsonify, render_template, abort
import os
from pathlib import Path
import google.generativeai as genai # Changed
from markupsafe import Markup
import markdown2  # To parse markdown
import re
import html  # Import for escaping special characters

app = Flask(__name__)

# Configure Gemini client
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    # This part is fine, a truly missing key should be an error
    raise ValueError("GEMINI_API_KEY environment variable not set.")
try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API configured successfully.") # Added for feedback
except Exception as e:
    # If configure fails (e.g. due to fake key format for testing),
    # print a warning but allow app to continue starting.
    # Subsequent API calls will then fail, which tests should handle.
    print(f"Warning: Gemini API configuration failed: {e}. App will start, but Gemini calls will likely fail.")

BASE_DIR = Path("RABBITHOLE/markdown")

def get_folder_structure(base_path):
    structure = []
    folders = []
    files = []

    # Separate directories and files
    for entry in os.scandir(base_path):
        if entry.is_dir():
            folders.append({
                'type': 'folder',
                'name': entry.name,
                'children': get_folder_structure(entry.path)
            })
        elif entry.is_file() and entry.name.endswith('.md'):
            relative_path = os.path.relpath(entry.path, BASE_DIR).replace('\\', '/')
            files.append({
                'type': 'file',
                'name': entry.name,
                'path': relative_path
            })

    # Sort folders and files alphabetically
    folders.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())

    # Combine folders and files, folders first
    structure.extend(folders)
    structure.extend(files)

    return structure

def read_document(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_document(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

@app.route('/')
def index():
    structure = get_folder_structure(BASE_DIR)
    return render_template('index.html', structure=structure)

@app.route('/view_document/<path:doc_path>')
def view_document(doc_path):
    doc_path = BASE_DIR / doc_path
    if not doc_path.is_file():
        abort(404, description="Document not found")

    content = read_document(doc_path)  # Fetch raw markdown content
    html_content = markdown2.markdown(content)  # Convert Markdown to HTML

    # Return both HTML and Markdown as JSON
    return jsonify({
        "html_content": html_content,
        "markdown_content": content
    })

@app.route('/edit_document', methods=['POST'])
def edit_document():
    doc_path = request.json.get('doc_path')
    new_content = request.json.get('content')
    full_path = BASE_DIR / doc_path

    if not full_path.is_file():
        return jsonify({"error": "Document not found"}), 404

    write_document(full_path, new_content)  # Save raw markdown directly
    return jsonify({"message": "Document updated successfully."})

def sanitize_filename(name):
    """Remove invalid characters and limit length for filename compatibility."""
    return re.sub(r'[<>:"/\\|?*]', '', name)[:50]

@app.route('/generate_document', methods=['POST'])
def generate_document():
    doc_path = request.json.get('doc_path')
    operation = request.json.get('operation', 'alter')
    context_text = request.json.get('context_text', '')

    full_path = BASE_DIR / doc_path

    if operation == 'alter' and full_path.is_file():
        prompt = f"Alter the following content:\n\n{read_document(full_path)}\n\nInstructions:\n{context_text}"
    else:
        prompt = f"Generate a new document using the following context:\n\n{context_text}"

    # Debug: Print the prompt that will be sent to Gemini
    #print("Generated Prompt for Gemini:", prompt)

    # Generate content using Gemini
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)

    # Debug: Print the full Gemini response to inspect
    #print("Gemini Response:", response)

    new_content = response.text # Changed

    # If we are generating a new document, we need to create a new file
    if operation == 'generate':
        # Use Gemini to generate a title
        title_prompt = f"Provide a short title based on the following context:\n\n{context_text}"
        #print("Generated Title Prompt for Gemini:", title_prompt)

        title_model = genai.GenerativeModel('gemini-pro') # Using gemini-pro for title too
        title_response = title_model.generate_content(title_prompt)

        # Debug: Print the title response to inspect
        print("Title Response:", title_response)

        title = title_response.text # Changed
        file_name = sanitize_filename(title.strip()) + ".md"

        # Construct the path for the new document
        new_doc_path = BASE_DIR / file_name

        # Ensure the directory exists
        os.makedirs(new_doc_path.parent, exist_ok=True)

        # Write the generated content to the new file
        write_document(new_doc_path, new_content)
        return jsonify({"message": f"Document '{file_name}' generated successfully.", "content": new_content})

    # If altering an existing document, write to the existing file
    write_document(full_path, new_content)
    return jsonify({"message": "Document updated successfully.", "content": new_content})

def render_folders(structure):
    html = '<ul>'
    for item in structure:
        if item['type'] == 'folder':
            folder_name = item['name']
            html += f'''
            <li class="folder-item">
                <div class="folder-header" onclick="toggleFolder(this)">
                    <i class="fas fa-chevron-right folder-icon"></i>
                    <span class="folder-name">{folder_name}</span>
                </div>
                <div class="folder-content">
                    {render_folders(item['children'])}
                </div>
            </li>
            '''
        elif item['type'] == 'file':
            file_name = item['name']
            file_path = item['path']
            html += f'''
            <li class="file-item" id="file-{file_path.replace("/", "-")}" onclick="loadMarkdown('{file_path}', event)">
                <i class="fas fa-file file-icon"></i>
                <span class="file-name">{file_name}</span>
            </li>
            '''
    html += '</ul>'
    return Markup(html)

app.jinja_env.globals.update(render_folders=render_folders)
if __name__ == '__main__':
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    app.run(debug=True, port=port)
