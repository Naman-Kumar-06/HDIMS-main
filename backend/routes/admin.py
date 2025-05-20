from flask import Blueprint, request, jsonify
from backend.auth.auth import token_required
from backend.db.mysql import execute_query, fetch_results
from backend.dsa.segment_tree import SegmentTree
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/generate_report', methods=['GET'])
@token_required
def generate_report(current_user):
    """Generate analytics report for administrators"""
    try:
        # Verify user is an admin
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Only administrators can access this endpoint'}), 403
        
        # Determine report period (last 30 days by default)
        days = request.args.get('days', default=30, type=int)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get report type
        report_type = request.args.get('type', default='general', type=str)
        
        if report_type == 'general':
            # General hospital statistics
            return generate_general_report(start_date, end_date)
        elif report_type == 'doctor':
            # Doctor performance report
            return generate_doctor_report(start_date, end_date)
        elif report_type == 'appointment':
            # Appointment statistics
            return generate_appointment_report(start_date, end_date)
        else:
            return jsonify({'message': 'Invalid report type'}), 400
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'message': f'Error generating report: {str(e)}'}), 500

def generate_general_report(start_date, end_date):
    """Generate general hospital statistics report"""
    # Total patients, doctors, and appointments
    query_total_patients = "SELECT COUNT(*) as count FROM patients"
    execute_query(query_total_patients)
    total_patients = fetch_results()[0]['count']
    
    query_total_doctors = "SELECT COUNT(*) as count FROM doctors"
    execute_query(query_total_doctors)
    total_doctors = fetch_results()[0]['count']
    
    query_total_appointments = "SELECT COUNT(*) as count FROM appointments"
    execute_query(query_total_appointments)
    total_appointments = fetch_results()[0]['count']
    
    # Recent appointments (within date range)
    query_recent_appointments = """
        SELECT COUNT(*) as count, status 
        FROM appointments 
        WHERE DATE(appointment_time) BETWEEN %s AND %s 
        GROUP BY status
    """
    params = (start_date, end_date)
    execute_query(query_recent_appointments, params)
    recent_appointments = fetch_results()
    
    # Format recent appointments
    appointment_stats = {
        'scheduled': 0,
        'completed': 0,
        'cancelled': 0
    }
    
    for row in recent_appointments:
        appointment_stats[row['status']] = row['count']
    
    # Specialization distribution
    query_specializations = """
        SELECT specialization, COUNT(*) as count 
        FROM doctors 
        GROUP BY specialization 
        ORDER BY count DESC
    """
    execute_query(query_specializations)
    specializations = fetch_results()
    
    # Performance metrics summary
    query_performance = """
        SELECT 
            AVG(avg_response_time) as avg_response,
            AVG(satisfaction_score) as avg_satisfaction
        FROM performance_metrics
        WHERE date BETWEEN %s AND %s
    """
    params = (start_date, end_date)
    execute_query(query_performance, params)
    performance = fetch_results()[0]
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': (end_date - start_date).days
        },
        'totals': {
            'patients': total_patients,
            'doctors': total_doctors,
            'appointments': total_appointments
        },
        'recent_appointments': appointment_stats,
        'specializations': specializations,
        'performance': {
            'avg_response_time': performance['avg_response'] if performance['avg_response'] else 0,
            'avg_satisfaction': performance['avg_satisfaction'] if performance['avg_satisfaction'] else 0
        }
    }), 200

def generate_doctor_report(start_date, end_date):
    """Generate doctor performance report"""
    # Get doctor performance metrics
    query_performance = """
        SELECT 
            d.doctor_id,
            d.name,
            d.specialization,
            AVG(pm.avg_response_time) as avg_response,
            AVG(pm.satisfaction_score) as avg_satisfaction,
            SUM(pm.patients_seen) as total_patients
        FROM doctors d
        LEFT JOIN performance_metrics pm ON d.doctor_id = pm.doctor_id
        WHERE pm.date BETWEEN %s AND %s OR pm.date IS NULL
        GROUP BY d.doctor_id, d.name, d.specialization
        ORDER BY avg_satisfaction DESC
    """
    params = (start_date, end_date)
    execute_query(query_performance, params)
    doctor_performance = fetch_results()
    
    # Get appointment counts per doctor
    query_appointments = """
        SELECT 
            d.doctor_id,
            COUNT(a.id) as total_appointments,
            SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM doctors d
        LEFT JOIN appointments a ON d.doctor_id = a.doctor_id AND DATE(a.appointment_time) BETWEEN %s AND %s
        GROUP BY d.doctor_id
    """
    params = (start_date, end_date)
    execute_query(query_appointments, params)
    appointment_stats = fetch_results()
    
    # Create a dictionary of appointment stats by doctor_id for easy lookup
    appointment_dict = {}
    for row in appointment_stats:
        appointment_dict[row['doctor_id']] = {
            'total_appointments': row['total_appointments'],
            'completed': row['completed'],
            'cancelled': row['cancelled']
        }
    
    # Combine data
    for doctor in doctor_performance:
        doctor_id = doctor['doctor_id']
        if doctor_id in appointment_dict:
            doctor.update(appointment_dict[doctor_id])
        else:
            doctor.update({
                'total_appointments': 0,
                'completed': 0,
                'cancelled': 0
            })
        
        # Calculate completion rate
        if doctor['total_appointments'] > 0:
            doctor['completion_rate'] = round((doctor['completed'] / doctor['total_appointments']) * 100, 2)
        else:
            doctor['completion_rate'] = 0
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': (end_date - start_date).days
        },
        'doctors': doctor_performance
    }), 200

def generate_appointment_report(start_date, end_date):
    """Generate appointment statistics report"""
    # Get daily appointment counts
    query_daily = """
        SELECT 
            DATE(appointment_time) as date,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM appointments
        WHERE DATE(appointment_time) BETWEEN %s AND %s
        GROUP BY DATE(appointment_time)
        ORDER BY date
    """
    params = (start_date, end_date)
    execute_query(query_daily, params)
    daily_stats = fetch_results()
    
    # Use SegmentTree for analyzing time ranges of appointment data
    # First, extract just the total appointments per day
    if daily_stats:
        dates = [row['date'].isoformat() for row in daily_stats]
        totals = [row['total'] for row in daily_stats]
        completed = [row['completed'] for row in daily_stats]
        
        # Create segment trees
        totals_tree = SegmentTree(totals, sum)
        max_tree = SegmentTree(totals, max)
        
        # Find busiest week (7-day period)
        busiest_week = {'start': 0, 'end': 0, 'total': 0}
        
        for i in range(len(totals) - 6):
            week_total = totals_tree.query(i, i + 6)
            if week_total > busiest_week['total']:
                busiest_week = {'start': i, 'end': i + 6, 'total': week_total}
        
        if busiest_week['total'] > 0:
            busiest_week['start_date'] = dates[busiest_week['start']]
            busiest_week['end_date'] = dates[busiest_week['end']]
        
        # Find the day with maximum appointments
        max_day_index = totals.index(max_tree.query(0, len(totals) - 1))
        max_day = {
            'date': dates[max_day_index],
            'total': totals[max_day_index]
        }
    else:
        busiest_week = {'total': 0}
        max_day = {'total': 0}
        dates = []
        totals = []
        completed = []
    
    # Get urgency distribution
    query_urgency = """
        SELECT 
            urgency,
            COUNT(*) as count
        FROM appointments
        WHERE DATE(appointment_time) BETWEEN %s AND %s
        GROUP BY urgency
        ORDER BY urgency
    """
    params = (start_date, end_date)
    execute_query(query_urgency, params)
    urgency_stats = fetch_results()
    
    # Calculate overall statistics
    total_appointments = sum(totals) if totals else 0
    total_completed = sum(completed) if completed else 0
    completion_rate = round((total_completed / total_appointments) * 100, 2) if total_appointments > 0 else 0
    
    return jsonify({
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': (end_date - start_date).days
        },
        'overall': {
            'total_appointments': total_appointments,
            'completion_rate': completion_rate
        },
        'busiest_week': busiest_week,
        'max_day': max_day,
        'daily_stats': daily_stats,
        'urgency_distribution': urgency_stats
    }), 200

@admin_bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    """Get all users (admin only)"""
    try:
        # Verify user is an admin
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Only administrators can access this endpoint'}), 403
        
        # Get all users
        query = "SELECT uid, email, role, created_at FROM users"
        execute_query(query)
        users = fetch_results()
        
        return jsonify({'users': users}), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({'message': f'Error getting users: {str(e)}'}), 500

@admin_bp.route('/update_performance', methods=['POST'])
@token_required
def update_performance(current_user):
    """Update doctor performance metrics (admin only)"""
    try:
        # Verify user is an admin
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Only administrators can access this endpoint'}), 403
        
        # Parse request data
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No input data provided'}), 400
        
        required_fields = ['doctor_id', 'date', 'avg_response_time', 'patients_seen', 'satisfaction_score']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Check if doctor exists
        query = "SELECT * FROM doctors WHERE doctor_id = %s"
        params = (data['doctor_id'],)
        execute_query(query, params)
        doctor = fetch_results()
        
        if not doctor:
            return jsonify({'message': 'Doctor not found'}), 404
        
        # Check if metrics already exist for this date
        query = "SELECT * FROM performance_metrics WHERE doctor_id = %s AND date = %s"
        params = (data['doctor_id'], data['date'])
        execute_query(query, params)
        existing = fetch_results()
        
        if existing:
            # Update existing metrics
            query = """
                UPDATE performance_metrics
                SET avg_response_time = %s, patients_seen = %s, satisfaction_score = %s
                WHERE doctor_id = %s AND date = %s
            """
            params = (
                data['avg_response_time'],
                data['patients_seen'],
                data['satisfaction_score'],
                data['doctor_id'],
                data['date']
            )
        else:
            # Insert new metrics
            query = """
                INSERT INTO performance_metrics 
                (doctor_id, date, avg_response_time, patients_seen, satisfaction_score)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                data['doctor_id'],
                data['date'],
                data['avg_response_time'],
                data['patients_seen'],
                data['satisfaction_score']
            )
        
        execute_query(query, params)
        
        return jsonify({'message': 'Performance metrics updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating performance metrics: {str(e)}")
        return jsonify({'message': f'Error updating performance metrics: {str(e)}'}), 500
