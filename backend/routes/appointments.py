from flask import Blueprint, request, jsonify
from backend.auth.auth import token_required
from backend.db.mysql import execute_query, fetch_results
from backend.dsa.minheap import MinHeap
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint
appointments_bp = Blueprint('appointments', __name__)

# Initialize urgency heap for appointment priority
appointment_heap = MinHeap()

@appointments_bp.route('/book', methods=['POST'])
@token_required
def book_appointment(current_user):
    """Book a new appointment"""
    try:
        # Check if user is a patient
        if current_user['role'] != 'patient':
            return jsonify({'message': 'Only patients can book appointments'}), 403
        
        # Get patient_id from the database
        query = "SELECT patient_id FROM patients WHERE uid = %s"
        params = (current_user['uid'],)
        execute_query(query, params)
        patient_result = fetch_results()
        
        if not patient_result:
            return jsonify({'message': 'Patient profile not found'}), 404
        
        patient_id = patient_result[0]['patient_id']
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No input data provided'}), 400
        
        required_fields = ['doctor_id', 'appointment_time', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        doctor_id = data['doctor_id']
        appointment_time = data['appointment_time']
        reason = data['reason']
        urgency = data.get('urgency', 0)  # Default urgency is 0 (lowest)
        
        # Check if doctor exists
        query = "SELECT * FROM doctors WHERE doctor_id = %s"
        params = (doctor_id,)
        execute_query(query, params)
        doctor_result = fetch_results()
        
        if not doctor_result:
            return jsonify({'message': 'Doctor not found'}), 404
        
        # Check for conflicting appointments
        query = """
            SELECT * FROM appointments 
            WHERE doctor_id = %s AND appointment_time = %s AND status != 'cancelled'
        """
        params = (doctor_id, appointment_time)
        execute_query(query, params)
        existing_appointments = fetch_results()
        
        if existing_appointments:
            return jsonify({'message': 'This time slot is already booked'}), 409
        
        # Insert appointment into database
        query = """
            INSERT INTO appointments 
            (patient_id, doctor_id, appointment_time, urgency, reason, status) 
            VALUES (%s, %s, %s, %s, %s, 'scheduled')
        """
        params = (patient_id, doctor_id, appointment_time, urgency, reason)
        appointment_id = execute_query(query, params)
        
        if not appointment_id:
            return jsonify({'message': 'Failed to book appointment'}), 500
        
        # Add to urgency heap for priority-based processing
        appointment_data = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'appointment_time': appointment_time,
            'reason': reason,
            'status': 'scheduled'
        }
        appointment_heap.insert(urgency, appointment_id, appointment_data)
        
        return jsonify({
            'message': 'Appointment booked successfully',
            'appointment_id': appointment_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return jsonify({'message': f'Error booking appointment: {str(e)}'}), 500

@appointments_bp.route('/list', methods=['GET'])
@token_required
def list_appointments(current_user):
    """List appointments for the current user based on their role"""
    try:
        user_id = current_user['uid']
        role = current_user['role']
        
        if role == 'patient':
            # Get patient_id
            query = "SELECT patient_id FROM patients WHERE uid = %s"
            params = (user_id,)
            execute_query(query, params)
            patient_result = fetch_results()
            
            if not patient_result:
                return jsonify({'message': 'Patient profile not found'}), 404
            
            patient_id = patient_result[0]['patient_id']
            
            # Get appointments for this patient
            query = """
                SELECT a.*, d.name as doctor_name, d.specialization 
                FROM appointments a 
                JOIN doctors d ON a.doctor_id = d.doctor_id 
                WHERE a.patient_id = %s
                ORDER BY a.appointment_time
            """
            params = (patient_id,)
            
        elif role == 'doctor':
            # Get doctor_id
            query = "SELECT doctor_id FROM doctors WHERE uid = %s"
            params = (user_id,)
            execute_query(query, params)
            doctor_result = fetch_results()
            
            if not doctor_result:
                return jsonify({'message': 'Doctor profile not found'}), 404
            
            doctor_id = doctor_result[0]['doctor_id']
            
            # Get appointments for this doctor
            query = """
                SELECT a.*, p.name as patient_name
                FROM appointments a 
                JOIN patients p ON a.patient_id = p.patient_id 
                WHERE a.doctor_id = %s
                ORDER BY a.appointment_time
            """
            params = (doctor_id,)
            
        elif role == 'admin':
            # Admins can see all appointments
            query = """
                SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization
                FROM appointments a 
                JOIN patients p ON a.patient_id = p.patient_id 
                JOIN doctors d ON a.doctor_id = d.doctor_id
                ORDER BY a.appointment_time
            """
            params = ()
            
        else:
            return jsonify({'message': 'Invalid role'}), 403
        
        execute_query(query, params)
        appointments = fetch_results()
        
        return jsonify({'appointments': appointments}), 200
        
    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        return jsonify({'message': f'Error listing appointments: {str(e)}'}), 500

@appointments_bp.route('/cancel/<int:appointment_id>', methods=['PUT'])
@token_required
def cancel_appointment(current_user, appointment_id):
    """Cancel an existing appointment"""
    try:
        # Check if the appointment exists
        query = "SELECT * FROM appointments WHERE id = %s"
        params = (appointment_id,)
        execute_query(query, params)
        appointment = fetch_results()
        
        if not appointment:
            return jsonify({'message': 'Appointment not found'}), 404
        
        appointment = appointment[0]
        
        # Check if user has permission to cancel
        user_id = current_user['uid']
        role = current_user['role']
        
        if role == 'patient':
            # Verify this is the patient's appointment
            query = "SELECT patient_id FROM patients WHERE uid = %s"
            params = (user_id,)
            execute_query(query, params)
            patient_result = fetch_results()
            
            if not patient_result or patient_result[0]['patient_id'] != appointment['patient_id']:
                return jsonify({'message': 'You do not have permission to cancel this appointment'}), 403
                
        elif role == 'doctor':
            # Verify this is the doctor's appointment
            query = "SELECT doctor_id FROM doctors WHERE uid = %s"
            params = (user_id,)
            execute_query(query, params)
            doctor_result = fetch_results()
            
            if not doctor_result or doctor_result[0]['doctor_id'] != appointment['doctor_id']:
                return jsonify({'message': 'You do not have permission to cancel this appointment'}), 403
                
        elif role != 'admin':
            return jsonify({'message': 'Invalid role'}), 403
        
        # Update appointment status to cancelled
        query = "UPDATE appointments SET status = 'cancelled' WHERE id = %s"
        params = (appointment_id,)
        execute_query(query, params)
        
        # Remove from urgency heap if it exists
        appointment_heap.remove(appointment_id)
        
        return jsonify({'message': 'Appointment cancelled successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return jsonify({'message': f'Error cancelling appointment: {str(e)}'}), 500

@appointments_bp.route('/update/<int:appointment_id>', methods=['PUT'])
@token_required
def update_appointment(current_user, appointment_id):
    """Update an existing appointment"""
    try:
        # Check if the appointment exists
        query = "SELECT * FROM appointments WHERE id = %s"
        params = (appointment_id,)
        execute_query(query, params)
        appointment = fetch_results()
        
        if not appointment:
            return jsonify({'message': 'Appointment not found'}), 404
        
        appointment = appointment[0]
        
        # Check if user has permission to update
        user_id = current_user['uid']
        role = current_user['role']
        
        if role == 'patient':
            # Verify this is the patient's appointment
            query = "SELECT patient_id FROM patients WHERE uid = %s"
            params = (user_id,)
            execute_query(query, params)
            patient_result = fetch_results()
            
            if not patient_result or patient_result[0]['patient_id'] != appointment['patient_id']:
                return jsonify({'message': 'You do not have permission to update this appointment'}), 403
                
        elif role == 'doctor':
            # Verify this is the doctor's appointment
            query = "SELECT doctor_id FROM doctors WHERE uid = %s"
            params = (user_id,)
            execute_query(query, params)
            doctor_result = fetch_results()
            
            if not doctor_result or doctor_result[0]['doctor_id'] != appointment['doctor_id']:
                return jsonify({'message': 'You do not have permission to update this appointment'}), 403
                
        elif role != 'admin':
            return jsonify({'message': 'Invalid role'}), 403
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No input data provided'}), 400
        
        # Create update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if 'appointment_time' in data:
            update_fields.append("appointment_time = %s")
            params.append(data['appointment_time'])
            
        if 'reason' in data:
            update_fields.append("reason = %s")
            params.append(data['reason'])
            
        if 'status' in data and role in ['doctor', 'admin']:
            # Only doctors and admins can update status
            update_fields.append("status = %s")
            params.append(data['status'])
            
        if 'urgency' in data and role in ['doctor', 'admin']:
            # Only doctors and admins can update urgency
            update_fields.append("urgency = %s")
            params.append(data['urgency'])
            
            # Update urgency in the heap
            appointment_heap.update_priority(appointment_id, data['urgency'])
        
        if not update_fields:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        # Complete the query and params
        query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE id = %s"
        params.append(appointment_id)
        
        execute_query(query, params)
        
        return jsonify({'message': 'Appointment updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        return jsonify({'message': f'Error updating appointment: {str(e)}'}), 500

@appointments_bp.route('/next', methods=['GET'])
@token_required
def get_next_appointment(current_user):
    """Get the next most urgent appointment (for doctors and admins)"""
    try:
        role = current_user['role']
        
        if role not in ['doctor', 'admin']:
            return jsonify({'message': 'Only doctors and admins can access this endpoint'}), 403
        
        # Get the most urgent appointment
        next_appointment = appointment_heap.get_min()
        
        if not next_appointment:
            return jsonify({'message': 'No appointments in queue'}), 404
        
        urgency, appointment_id, appointment_data = next_appointment
        
        # Get full appointment details from database
        query = """
            SELECT a.*, p.name as patient_name, d.name as doctor_name
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.patient_id 
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.id = %s
        """
        params = (appointment_id,)
        execute_query(query, params)
        appointment = fetch_results()
        
        if not appointment:
            # This shouldn't happen, but handle it anyway
            appointment_heap.extract_min()  # Remove inconsistent entry
            return jsonify({'message': 'Appointment not found in database'}), 404
        
        return jsonify({'appointment': appointment[0], 'urgency': urgency}), 200
        
    except Exception as e:
        logger.error(f"Error getting next appointment: {str(e)}")
        return jsonify({'message': f'Error getting next appointment: {str(e)}'}), 500
