import jwt
from datetime import datetime, timedelta, timezone
import os
from functools import wraps
from flask import request, jsonify, g # g for storing current user

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-default-secret-key-please-change-in-prod") # Ensure this is strong in production
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Default expiry time

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token expired"
    except jwt.InvalidTokenError:
        return "Invalid token"
    except Exception as e:
        # Log the exception e for server-side debugging if needed
        print(f"Token decoding error: {e}")
        return f"Token decoding error: An unexpected issue occurred."


# Decorator for protected routes
def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header missing or invalid"}), 401
        
        token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None
        if not token:
            return jsonify({"message": "Token missing from Authorization header"}), 401
            
        payload = decode_access_token(token)

        if isinstance(payload, str): # Error string from decode_access_token
            return jsonify({"message": payload}), 401 # Return the error message (e.g., "Token expired")
        
        # 'sub' is conventional for subject (user_id/username)
        # In our case, it will be the username of the authenticated user
        current_user_subject = payload.get("sub") 
        if not current_user_subject:
            return jsonify({"message": "Token missing user identifier (sub)"}), 401
        
        g.current_user_id = current_user_subject # Store the username as current_user_id in Flask's g object
        
        return f(*args, **kwargs)
    return decorated_function
