import json
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)

def format_response(data):
    """
    Format a response to ensure all datetime objects are serialized properly.
    
    Args:
        data (dict): Response data
        
    Returns:
        str: JSON string with properly formatted dates
    """
    return json.dumps(data, cls=DateTimeEncoder)

def validate_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (bool, str) - (True if valid, error message if invalid)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    
    return True, None

def calculate_age(dob):
    """
    Calculate age from date of birth.
    
    Args:
        dob (str or date): Date of birth in YYYY-MM-DD format or date object
        
    Returns:
        int: Age in years
    """
    if isinstance(dob, str):
        dob = datetime.datetime.strptime(dob, '%Y-%m-%d').date()
    
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def format_date(date_str, input_format='%Y-%m-%d', output_format='%B %d, %Y'):
    """
    Format a date string from one format to another.
    
    Args:
        date_str (str): Date string to format
        input_format (str): Input date format
        output_format (str): Output date format
        
    Returns:
        str: Formatted date string
    """
    if not date_str:
        return ""
    
    try:
        date_obj = datetime.datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        logger.error(f"Invalid date format: {date_str}")
        return date_str

def format_time(time_str, input_format='%Y-%m-%d %H:%M:%S', output_format='%I:%M %p, %b %d'):
    """
    Format a time string from one format to another.
    
    Args:
        time_str (str): Time string to format
        input_format (str): Input time format
        output_format (str): Output time format
        
    Returns:
        str: Formatted time string
    """
    if not time_str:
        return ""
    
    try:
        time_obj = datetime.datetime.strptime(time_str, input_format)
        return time_obj.strftime(output_format)
    except ValueError:
        logger.error(f"Invalid time format: {time_str}")
        return time_str

def sanitize_input(text):
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text (str): Input text to sanitize
        
    Returns:
        str: Sanitized text
    """
    import html
    
    if not text:
        return ""
    
    # HTML escape to prevent XSS
    return html.escape(str(text))
