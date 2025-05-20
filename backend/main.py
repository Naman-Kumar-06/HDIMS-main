import os
import logging
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from backend.auth.auth import token_required
from backend.db.mysql import initialize_db
from backend.routes.appointments import appointments_bp
from backend.routes.doctors import doctors_bp
from backend.routes.patients import patients_bp
from backend.routes.admin import admin_bp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.environ.get("SESSION_SECRET")

# Enable CORS
CORS(app)

# Initialize database
initialize_db()

# Register blueprints
app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
app.register_blueprint(doctors_bp, url_prefix='/api/doctors')
app.register_blueprint(patients_bp, url_prefix='/api/patients')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route('/')
def index():
    """Serve the index page"""
    return app.send_static_file('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Login route"""
    from backend.auth.auth import login
    
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Invalid request data'}), 400
    
    token, error = login(data['email'], data['password'])
    
    if error:
        return jsonify({'message': error}), 401
    
    # Get role from token
    from backend.auth.auth import decode_token
    payload = decode_token(token)
    role = payload['role']
    uid = payload['uid']
    
    # Get user profile info based on role
    user_info = {'uid': uid, 'email': data['email'], 'role': role}
    
    if role == 'patient':
        from backend.db.mysql import execute_query, fetch_results
        
        query = "SELECT patient_id, name FROM patients WHERE uid = %s"
        params = (uid,)
        execute_query(query, params)
        patient = fetch_results()
        
        if patient:
            user_info['patient_id'] = patient[0]['patient_id']
            user_info['name'] = patient[0]['name']
            
    elif role == 'doctor':
        from backend.db.mysql import execute_query, fetch_results
        
        query = "SELECT doctor_id, name, specialization FROM doctors WHERE uid = %s"
        params = (uid,)
        execute_query(query, params)
        doctor = fetch_results()
        
        if doctor:
            user_info['doctor_id'] = doctor[0]['doctor_id']
            user_info['name'] = doctor[0]['name']
            user_info['specialization'] = doctor[0]['specialization']
    
    return jsonify({'token': token, 'user': user_info}), 200

@app.route('/api/signup', methods=['POST'])
def signup():
    """Signup route"""
    from backend.auth.auth import signup
    
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data or 'role' not in data:
        return jsonify({'message': 'Invalid request data'}), 400
    
    if data['role'] not in ['patient', 'doctor', 'admin']:
        return jsonify({'message': 'Invalid role'}), 400
    
    token, error = signup(data['email'], data['password'], data['role'])
    
    if error:
        return jsonify({'message': error}), 400
    
    # Get UID from token
    from backend.auth.auth import decode_token
    payload = decode_token(token)
    
    return jsonify({
        'message': 'User created successfully',
        'token': token,
        'uid': payload['uid'],
        'role': payload['role']
    }), 201

@app.route('/api/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verify token and return user data"""
    return jsonify({'user': current_user}), 200

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'message': 'API endpoint not found'}), 404
    return app.send_static_file('index.html')

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
