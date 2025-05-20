from functools import wraps
from flask import request, jsonify
from backend.auth.auth import verify_token
from backend.db.mysql import execute_query, fetch_results
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def role_required(allowed_roles):
    """
    Decorator to restrict access to certain routes based on user role.
    
    Args:
        allowed_roles (list): List of roles allowed to access the route
        
    Returns:
        function: Decorated route function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get the token from the Authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'message': 'Missing or invalid Authorization header'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify the token
            payload = verify_token(token)
            
            if not payload:
                return jsonify({'message': 'Invalid or expired token'}), 401
            
            # Check if user has required role
            if payload['role'] not in allowed_roles:
                return jsonify({'message': 'You do not have permission to access this resource'}), 403
            
            # Pass the user payload to the route function
            return f(payload, *args, **kwargs)
        
        return decorated_function
    
    return decorator

def admin_required(f):
    """
    Decorator to restrict access to admin users only.
    
    Returns:
        function: Decorated route function
    """
    return role_required(['admin'])(f)

def doctor_required(f):
    """
    Decorator to restrict access to doctor users only.
    
    Returns:
        function: Decorated route function
    """
    return role_required(['doctor', 'admin'])(f)

def patient_required(f):
    """
    Decorator to restrict access to patient users only.
    
    Returns:
        function: Decorated route function
    """
    return role_required(['patient', 'admin'])(f)
