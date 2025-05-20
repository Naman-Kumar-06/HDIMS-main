import os
import jwt
import datetime
import bcrypt
from functools import wraps
from flask import request, jsonify
from backend.db.mysql import execute_query, fetch_results

# Mock Firebase authentication functions

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "hdims_secret_key")

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    """Check if password matches the hashed password"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_token(user_id, role):
    """Generate a JWT token (similar to Firebase)"""
    payload = {
        'uid': user_id,
        'role': role,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def decode_token(token):
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def signup(email, password, role):
    """Sign up a new user"""
    # Check if user already exists
    query = "SELECT * FROM users WHERE email = %s"
    params = (email,)
    execute_query(query, params)
    existing_user = fetch_results()
    
    if existing_user:
        return None, "User with this email already exists"
    
    # Create new user
    hashed_password = hash_password(password)
    query = "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)"
    params = (email, hashed_password, role)
    
    try:
        user_id = execute_query(query, params)
        
        # Get the newly created user
        query = "SELECT * FROM users WHERE uid = %s"
        params = (user_id,)
        execute_query(query, params)
        user = fetch_results()[0]
        
        # Generate token
        token = generate_token(user['uid'], user['role'])
        
        return token, None
    except Exception as e:
        return None, str(e)

def login(email, password):
    """Login a user"""
    query = "SELECT * FROM users WHERE email = %s"
    params = (email,)
    execute_query(query, params)
    results = fetch_results()
    
    if not results:
        return None, "User not found"
    
    user = results[0]
    
    if not check_password(password, user['password_hash']):
        return None, "Invalid password"
    
    # Generate token
    token = generate_token(user['uid'], user['role'])
    
    return token, None

def verify_token(token):
    """Verify a JWT token"""
    payload = decode_token(token)
    if not payload:
        return None
    
    # Check if user exists
    query = "SELECT * FROM users WHERE uid = %s"
    params = (payload['uid'],)
    execute_query(query, params)
    results = fetch_results()
    
    if not results:
        return None
    
    return payload

def token_required(f):
    """Decorator to protect routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(payload, *args, **kwargs)
    
    return decorated
