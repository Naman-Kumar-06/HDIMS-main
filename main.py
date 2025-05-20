import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import secrets
from models import db, User, Patient, Doctor, Appointment, PerformanceMetric, MedicalRecord

# Create Flask app
app = Flask(__name__, 
            static_folder='frontend',
            static_url_path='')

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345678@localhost:5432/hdims_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Initialize database with the app
db.init_app(app)

# Define routes
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/dashboard_patient.html')
def patient_dashboard():
    return app.send_static_file('dashboard_patient.html')

@app.route('/dashboard_doctor.html')
def doctor_dashboard():
    return app.send_static_file('dashboard_doctor.html')

@app.route('/dashboard_admin.html')
def admin_dashboard():
    return app.send_static_file('dashboard_admin.html')

# API routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    # Generate token
    token = secrets.token_hex(16)
    
    # Get additional user info based on role
    user_info = {
        'uid': user.id,
        'email': user.email,
        'role': user.role,
        'name': user.name or user.email.split('@')[0]
    }
    
    # Add role-specific IDs
    if user.role == 'patient':
        patient = Patient.query.filter_by(user_id=user.id).first()
        if patient:
            user_info['patient_id'] = patient.id
    elif user.role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            user_info['doctor_id'] = doctor.id
            user_info['specialization'] = doctor.specialization
    
    return jsonify({
        'token': token,
        'user': user_info
    })

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('role'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    # Create new user
    user = User()
    user.email = data['email']
    user.role = data['role']
    user.name = data.get('name', user.email.split('@')[0])  # Use part of email as name if not provided
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create role-specific record
    if user.role == 'patient':
        patient = Patient()
        patient.user_id = user.id
        db.session.add(patient)
        db.session.commit()
        patient_id = patient.id
    elif user.role == 'doctor':
        doctor = Doctor()
        doctor.user_id = user.id
        doctor.specialization = data.get('specialization', 'General')
        db.session.add(doctor)
        db.session.commit()
        doctor_id = doctor.id
    
    # Generate token
    token = secrets.token_hex(16)
    
    return jsonify({
        'token': token,
        'uid': user.id,
        'role': user.role
    })

@app.route('/api/verify', methods=['GET'])
def verify():
    # Get token from header
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Missing or invalid token'}), 401
    
    # Extract token
    token = auth_header.split(' ')[1]
    
    # In a real app, you would verify the JWT token here
    # For demonstration, we'll just return success
    
    # Simulate getting user from token
    # In a real app, you'd decode the token and get the user ID
    
    # For testing, return logged-in user based on admin@hdims.com
    user = User.query.filter_by(email='admin@hdims.com').first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Get additional user info based on role
    user_info = {
        'uid': user.id,
        'email': user.email,
        'role': user.role,
        'name': user.name or user.email.split('@')[0]
    }
    
    # Add role-specific IDs
    if user.role == 'patient':
        patient = Patient.query.filter_by(user_id=user.id).first()
        if patient:
            user_info['patient_id'] = patient.id
    elif user.role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            user_info['doctor_id'] = doctor.id
            user_info['specialization'] = doctor.specialization
    
    return jsonify({
        'user': user_info
    })

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'message': 'Internal server error'}), 500

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create initial admin user if not exists
    if not User.query.filter_by(email='admin@hdims.com').first():
        admin = User()
        admin.email = 'admin@hdims.com'
        admin.role = 'admin'
        admin.name = 'Admin User'
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("Created admin user: admin@hdims.com / admin123")
        
    # Create sample doctor if not exists
    if not User.query.filter_by(email='doctor@hdims.com').first():
        doctor_user = User()
        doctor_user.email = 'doctor@hdims.com'
        doctor_user.role = 'doctor'
        doctor_user.name = 'Dr. John Smith'
        doctor_user.set_password('doctor123')
        db.session.add(doctor_user)
        db.session.commit()
        
        # Create doctor profile
        doctor = Doctor()
        doctor.user_id = doctor_user.id
        doctor.specialization = 'Cardiology'
        doctor.license_number = 'MD12345'
        doctor.experience_years = 10
        doctor.availability = 5
        doctor.rating = 4.8
        db.session.add(doctor)
        db.session.commit()
        
        print("Created doctor user: doctor@hdims.com / doctor123")
        
    # Create sample patient if not exists
    if not User.query.filter_by(email='patient@hdims.com').first():
        patient_user = User()
        patient_user.email = 'patient@hdims.com'
        patient_user.role = 'patient'
        patient_user.name = 'Jane Doe'
        patient_user.set_password('patient123')
        db.session.add(patient_user)
        db.session.commit()
        
        # Create patient profile
        patient = Patient()
        patient.user_id = patient_user.id
        patient.gender = 'Female'
        patient.blood_type = 'O+'
        patient.medical_history = 'No major issues'
        db.session.add(patient)
        db.session.commit()
        
        print("Created patient user: patient@hdims.com / patient123")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)