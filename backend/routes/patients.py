from flask import Blueprint, request, jsonify
from backend.auth.auth import token_required
from backend.db.mysql import execute_query, fetch_results
from backend.dsa.trie import Trie
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint
patients_bp = Blueprint('patients', __name__)

# Initialize Trie for patient search
patient_trie = Trie()

def load_patients_into_trie():
    """Load all patients into the trie for autocomplete search"""
    try:
        # Get all patients
        query = "SELECT patient_id, name FROM patients"
        execute_query(query)
        patients = fetch_results()
        
        # Reset trie
        global patient_trie
        patient_trie = Trie()
        
        # Add each patient to trie
        for patient in patients:
            patient_trie.insert(patient['name'], patient['patient_id'])
            
            # Also add each word in the name separately for better searching
            words = patient['name'].split()
            for word in words:
                if len(word) > 2:  # Only add words with at least 3 characters
                    patient_trie.insert(word, patient['patient_id'])
        
        logger.debug(f"Loaded {len(patients)} patients into search trie")
        
    except Exception as e:
        logger.error(f"Error loading patients into trie: {str(e)}")

@patients_bp.route('/search', methods=['GET'])
@token_required
def search_patients(current_user):
    """Search for patients with autocomplete functionality"""
    try:
        # Only doctors and admins can search patients
        if current_user['role'] not in ['doctor', 'admin']:
            return jsonify({'message': 'You do not have permission to search patients'}), 403
        
        # Get query parameter
        query_param = request.args.get('q', default='', type=str)
        
        if not query_param or len(query_param) < 2:
            return jsonify({'message': 'Search query must be at least 2 characters'}), 400
        
        # Refresh the trie with latest data
        load_patients_into_trie()
        
        # Search in trie
        results = patient_trie.starts_with(query_param)
        
        # Get full patient info for results
        patient_ids = list(set([patient_id for _, patient_id in results]))
        
        if not patient_ids:
            return jsonify({'patients': []}), 200
        
        # Format for SQL IN clause
        placeholders = ', '.join(['%s'] * len(patient_ids))
        query = f"""
            SELECT p.patient_id, p.name, p.gender, p.contact, 
                  (SELECT COUNT(*) FROM appointments a WHERE a.patient_id = p.patient_id) as appointment_count
            FROM patients p
            WHERE p.patient_id IN ({placeholders})
        """
        
        execute_query(query, patient_ids)
        patients = fetch_results()
        
        return jsonify({'patients': patients}), 200
        
    except Exception as e:
        logger.error(f"Error searching patients: {str(e)}")
        return jsonify({'message': f'Error searching patients: {str(e)}'}), 500

@patients_bp.route('/detail/<int:patient_id>', methods=['GET'])
@token_required
def patient_detail(current_user, patient_id):
    """Get detailed information about a specific patient"""
    try:
        # Only doctors and admins can view patient details
        # or the patient themselves
        role = current_user['role']
        
        if role == 'patient':
            # Verify this is the patient's own profile
            query = "SELECT uid FROM patients WHERE patient_id = %s"
            params = (patient_id,)
            execute_query(query, params)
            result = fetch_results()
            
            if not result or result[0]['uid'] != current_user['uid']:
                return jsonify({'message': 'You do not have permission to view this profile'}), 403
        
        elif role not in ['doctor', 'admin']:
            return jsonify({'message': 'You do not have permission to view patient details'}), 403
        
        # Get patient information
        query = "SELECT * FROM patients WHERE patient_id = %s"
        params = (patient_id,)
        execute_query(query, params)
        patient = fetch_results()
        
        if not patient:
            return jsonify({'message': 'Patient not found'}), 404
        
        patient = patient[0]
        
        # Get patient's appointment history
        query = """
            SELECT a.*, d.name as doctor_name, d.specialization
            FROM appointments a 
            JOIN doctors d ON a.doctor_id = d.doctor_id 
            WHERE a.patient_id = %s
            ORDER BY a.appointment_time DESC
        """
        params = (patient_id,)
        execute_query(query, params)
        appointments = fetch_results()
        
        return jsonify({
            'patient': patient,
            'appointments': appointments
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting patient details: {str(e)}")
        return jsonify({'message': f'Error getting patient details: {str(e)}'}), 500

@patients_bp.route('/register', methods=['POST'])
def register_patient():
    """Register a new patient"""
    try:
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No input data provided'}), 400
        
        required_fields = ['name', 'email', 'password', 'dob', 'gender', 'contact', 'address']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # First create user account
        from backend.auth.auth import signup
        
        token, error = signup(data['email'], data['password'], 'patient')
        
        if error:
            return jsonify({'message': f'Error creating user account: {error}'}), 400
        
        # Get UID from token
        from backend.auth.auth import decode_token
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'message': 'Error decoding token'}), 500
        
        uid = payload['uid']
        
        # Create patient profile
        query = """
            INSERT INTO patients (uid, name, dob, gender, contact, address, history)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            uid, 
            data['name'], 
            data['dob'], 
            data['gender'], 
            data['contact'], 
            data['address'], 
            data.get('history', '')
        )
        patient_id = execute_query(query, params)
        
        if not patient_id:
            return jsonify({'message': 'Failed to create patient profile'}), 500
        
        # Add to search trie
        patient_trie.insert(data['name'], patient_id)
        
        return jsonify({
            'message': 'Patient registered successfully',
            'patient_id': patient_id,
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering patient: {str(e)}")
        return jsonify({'message': f'Error registering patient: {str(e)}'}), 500

@patients_bp.route('/update/<int:patient_id>', methods=['PUT'])
@token_required
def update_patient(current_user, patient_id):
    """Update patient information"""
    try:
        # Check if this is the patient's own profile or a doctor/admin
        user_id = current_user['uid']
        role = current_user['role']
        
        if role == 'patient':
            # Verify this is the patient's own profile
            query = "SELECT uid FROM patients WHERE patient_id = %s"
            params = (patient_id,)
            execute_query(query, params)
            result = fetch_results()
            
            if not result or result[0]['uid'] != user_id:
                return jsonify({'message': 'You do not have permission to update this profile'}), 403
                
        elif role not in ['doctor', 'admin']:
            return jsonify({'message': 'You do not have permission to update patient profiles'}), 403
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No input data provided'}), 400
        
        # Create update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if 'name' in data:
            update_fields.append("name = %s")
            params.append(data['name'])
            
        if 'dob' in data:
            update_fields.append("dob = %s")
            params.append(data['dob'])
            
        if 'gender' in data:
            update_fields.append("gender = %s")
            params.append(data['gender'])
            
        if 'contact' in data:
            update_fields.append("contact = %s")
            params.append(data['contact'])
            
        if 'address' in data:
            update_fields.append("address = %s")
            params.append(data['address'])
            
        if 'history' in data and role in ['doctor', 'admin']:
            # Only doctors and admins can update medical history
            update_fields.append("history = %s")
            params.append(data['history'])
        
        if not update_fields:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        # Complete the query and params
        query = f"UPDATE patients SET {', '.join(update_fields)} WHERE patient_id = %s"
        params.append(patient_id)
        
        execute_query(query, params)
        
        # If name was updated, update in trie
        if 'name' in data:
            # Refresh the trie completely (simpler than targeted update)
            load_patients_into_trie()
        
        return jsonify({'message': 'Patient information updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating patient: {str(e)}")
        return jsonify({'message': f'Error updating patient: {str(e)}'}), 500
