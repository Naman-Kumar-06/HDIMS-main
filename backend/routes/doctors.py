from flask import Blueprint, request, jsonify
from backend.auth.auth import token_required
from backend.db.mysql import execute_query, fetch_results
from backend.dsa.maxheap import MaxHeap
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint
doctors_bp = Blueprint('doctors', __name__)

# Initialize maxheap for doctor availability
doctor_availability_heap = MaxHeap()

def load_doctors_into_heap():
    """Load all doctors and their availability into the max heap"""
    try:
        # Get all doctors
        query = "SELECT * FROM doctors"
        execute_query(query)
        doctors = fetch_results()
        
        # Clear existing heap
        while not doctor_availability_heap.is_empty():
            doctor_availability_heap.extract_max()
        
        # Calculate availability score for each doctor and add to heap
        for doctor in doctors:
            doctor_id = doctor['doctor_id']
            
            # Count scheduled appointments for the doctor
            query = """
                SELECT COUNT(*) as appointment_count 
                FROM appointments 
                WHERE doctor_id = %s AND status = 'scheduled'
            """
            params = (doctor_id,)
            execute_query(query, params)
            result = fetch_results()
            
            appointment_count = result[0]['appointment_count'] if result else 0
            
            # Higher availability score means more available
            # Inverse relationship with appointment count
            availability_score = 100 - min(appointment_count * 5, 95)  # Cap at 5, minimum score of 5
            
            # Insert into max heap
            doctor_availability_heap.insert(availability_score, doctor_id, doctor)
            
        logger.debug(f"Loaded {len(doctors)} doctors into availability heap")
        
    except Exception as e:
        logger.error(f"Error loading doctors into heap: {str(e)}")

@doctors_bp.route('/available', methods=['GET'])
def available_doctors():
    """Get a list of available doctors sorted by availability"""
    try:
        # Refresh the heap with latest data
        load_doctors_into_heap()
        
        # Get limit parameter, default is 10
        limit = request.args.get('limit', default=10, type=int)
        
        # Get specialization filter if provided
        specialization = request.args.get('specialization', default=None, type=str)
        
        # Get top N doctors from heap
        top_doctors = doctor_availability_heap.get_top_n(limit)
        
        # Format the response
        available_doctors = []
        for availability, doctor_id, doctor_data in top_doctors:
            # Apply specialization filter if provided
            if specialization and doctor_data['specialization'].lower() != specialization.lower():
                continue
                
            doctor_info = {
                'doctor_id': doctor_id,
                'name': doctor_data['name'],
                'specialization': doctor_data['specialization'],
                'availability_score': availability,
                'availability': doctor_data['availability']
            }
            available_doctors.append(doctor_info)
        
        return jsonify({'doctors': available_doctors}), 200
        
    except Exception as e:
        logger.error(f"Error getting available doctors: {str(e)}")
        return jsonify({'message': f'Error getting available doctors: {str(e)}'}), 500

@doctors_bp.route('/all', methods=['GET'])
def all_doctors():
    """Get a list of all doctors"""
    try:
        query = "SELECT * FROM doctors"
        execute_query(query)
        doctors = fetch_results()
        
        return jsonify({'doctors': doctors}), 200
        
    except Exception as e:
        logger.error(f"Error getting doctors: {str(e)}")
        return jsonify({'message': f'Error getting doctors: {str(e)}'}), 500

@doctors_bp.route('/detail/<int:doctor_id>', methods=['GET'])
def doctor_detail(doctor_id):
    """Get detailed information about a specific doctor"""
    try:
        # Get doctor information
        query = "SELECT * FROM doctors WHERE doctor_id = %s"
        params = (doctor_id,)
        execute_query(query, params)
        doctor = fetch_results()
        
        if not doctor:
            return jsonify({'message': 'Doctor not found'}), 404
        
        doctor = doctor[0]
        
        # Get doctor's upcoming appointments (if token provided and authorized)
        auth_header = request.headers.get('Authorization')
        upcoming_appointments = []
        
        if auth_header and auth_header.startswith('Bearer '):
            from backend.auth.auth import verify_token
            
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            
            if payload and payload['role'] in ['doctor', 'admin']:
                query = """
                    SELECT a.*, p.name as patient_name
                    FROM appointments a 
                    JOIN patients p ON a.patient_id = p.patient_id 
                    WHERE a.doctor_id = %s AND a.status = 'scheduled'
                    ORDER BY a.appointment_time
                """
                params = (doctor_id,)
                execute_query(query, params)
                upcoming_appointments = fetch_results()
        
        # Get doctor's performance metrics
        query = """
            SELECT AVG(avg_response_time) as avg_response, 
                   AVG(satisfaction_score) as avg_satisfaction
            FROM performance_metrics
            WHERE doctor_id = %s
        """
        params = (doctor_id,)
        execute_query(query, params)
        performance = fetch_results()
        
        performance_data = {
            'avg_response_time': performance[0]['avg_response'] if performance and performance[0]['avg_response'] else 0,
            'avg_satisfaction': performance[0]['avg_satisfaction'] if performance and performance[0]['avg_satisfaction'] else 0
        }
        
        response = {
            'doctor': doctor,
            'performance': performance_data
        }
        
        if upcoming_appointments:
            response['upcoming_appointments'] = upcoming_appointments
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting doctor details: {str(e)}")
        return jsonify({'message': f'Error getting doctor details: {str(e)}'}), 500

@doctors_bp.route('/register', methods=['POST'])
@token_required
def register_doctor(current_user):
    """Register a new doctor (admin only)"""
    try:
        # Check if user is an admin
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Only admins can register doctors'}), 403
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No input data provided'}), 400
        
        required_fields = ['name', 'specialization', 'contact', 'availability', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # First create user account
        from backend.auth.auth import signup
        
        token, error = signup(data['email'], data['password'], 'doctor')
        
        if error:
            return jsonify({'message': f'Error creating user account: {error}'}), 400
        
        # Get UID from token
        from backend.auth.auth import decode_token
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'message': 'Error decoding token'}), 500
        
        uid = payload['uid']
        
        # Create doctor profile
        query = """
            INSERT INTO doctors (uid, name, specialization, contact, availability)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (uid, data['name'], data['specialization'], data['contact'], data['availability'])
        doctor_id = execute_query(query, params)
        
        if not doctor_id:
            return jsonify({'message': 'Failed to create doctor profile'}), 500
        
        # Add to availability heap
        availability_score = 100  # New doctor starts with high availability
        doctor_data = {
            'doctor_id': doctor_id,
            'name': data['name'],
            'specialization': data['specialization'],
            'contact': data['contact'],
            'availability': data['availability']
        }
        doctor_availability_heap.insert(availability_score, doctor_id, doctor_data)
        
        return jsonify({
            'message': 'Doctor registered successfully',
            'doctor_id': doctor_id,
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering doctor: {str(e)}")
        return jsonify({'message': f'Error registering doctor: {str(e)}'}), 500

@doctors_bp.route('/update/<int:doctor_id>', methods=['PUT'])
@token_required
def update_doctor(current_user, doctor_id):
    """Update doctor information"""
    try:
        # Check if this is the doctor's own profile or an admin
        user_id = current_user['uid']
        role = current_user['role']
        
        if role == 'doctor':
            # Verify this is the doctor's own profile
            query = "SELECT uid FROM doctors WHERE doctor_id = %s"
            params = (doctor_id,)
            execute_query(query, params)
            result = fetch_results()
            
            if not result or result[0]['uid'] != user_id:
                return jsonify({'message': 'You do not have permission to update this profile'}), 403
                
        elif role != 'admin':
            return jsonify({'message': 'Only doctors can update their own profile or admins can update any profile'}), 403
        
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
            
        if 'specialization' in data:
            update_fields.append("specialization = %s")
            params.append(data['specialization'])
            
        if 'contact' in data:
            update_fields.append("contact = %s")
            params.append(data['contact'])
            
        if 'availability' in data:
            update_fields.append("availability = %s")
            params.append(data['availability'])
        
        if not update_fields:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        # Complete the query and params
        query = f"UPDATE doctors SET {', '.join(update_fields)} WHERE doctor_id = %s"
        params.append(doctor_id)
        
        execute_query(query, params)
        
        # Update in availability heap if doctor exists there
        if not doctor_availability_heap.remove(doctor_id):
            # If doctor wasn't in heap, refresh the heap
            load_doctors_into_heap()
        else:
            # Get updated doctor information
            query = "SELECT * FROM doctors WHERE doctor_id = %s"
            params = (doctor_id,)
            execute_query(query, params)
            doctor = fetch_results()[0]
            
            # Calculate availability score
            query = """
                SELECT COUNT(*) as appointment_count 
                FROM appointments 
                WHERE doctor_id = %s AND status = 'scheduled'
            """
            params = (doctor_id,)
            execute_query(query, params)
            result = fetch_results()
            
            appointment_count = result[0]['appointment_count'] if result else 0
            availability_score = 100 - min(appointment_count * 5, 95)
            
            # Add back to heap
            doctor_availability_heap.insert(availability_score, doctor_id, doctor)
        
        return jsonify({'message': 'Doctor information updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating doctor: {str(e)}")
        return jsonify({'message': f'Error updating doctor: {str(e)}'}), 500
