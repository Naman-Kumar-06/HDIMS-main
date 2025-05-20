import os
import mysql.connector
from mysql.connector import Error
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "hdims")

# Create a database connection pool
connection_pool = None

def initialize_db():
    """Initialize the database connection pool and create tables if they don't exist"""
    global connection_pool
    
    try:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="hdims_pool",
            pool_size=5,
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        logger.info("Connection pool created successfully")
        
        # Create database tables if they don't exist
        create_tables()
        
    except Error as e:
        logger.error(f"Error while connecting to MySQL: {e}")

def get_connection():
    """Get a connection from the pool"""
    global connection_pool
    
    if connection_pool is None:
        initialize_db()
    
    try:
        return connection_pool.get_connection()
    except Error as e:
        logger.error(f"Error while getting connection from pool: {e}")
        return None

def create_tables():
    """Create necessary tables if they don't exist"""
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            uid INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('patient', 'doctor', 'admin') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INT AUTO_INCREMENT PRIMARY KEY,
            uid INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            dob DATE,
            gender ENUM('male', 'female', 'other'),
            contact VARCHAR(20),
            address TEXT,
            history TEXT,
            FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id INT AUTO_INCREMENT PRIMARY KEY,
            uid INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            specialization VARCHAR(255) NOT NULL,
            contact VARCHAR(20),
            availability TEXT,
            FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            doctor_id INT NOT NULL,
            appointment_time DATETIME NOT NULL,
            urgency INT DEFAULT 0,
            reason TEXT,
            status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hospital_id INT DEFAULT 1,
            doctor_id INT NOT NULL,
            date DATE NOT NULL,
            avg_response_time FLOAT,
            patients_seen INT DEFAULT 0,
            satisfaction_score FLOAT DEFAULT 0,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
        )
        """
    ]
    
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            for table_query in tables:
                cursor.execute(table_query)
                
            connection.commit()
            logger.info("Tables created successfully")
            
        except Error as e:
            logger.error(f"Error creating tables: {e}")
        finally:
            cursor.close()
            connection.close()

def execute_query(query, params=None):
    """Execute a query with parameters and return the last row id if applicable"""
    connection = get_connection()
    cursor = None
    last_row_id = None
    
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            
            # Check if this is an INSERT query that would have an auto-increment ID
            if query.strip().upper().startswith("INSERT"):
                last_row_id = cursor.lastrowid
                
            logger.debug(f"Query executed successfully: {query}")
            return last_row_id
            
        except Error as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            connection.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            connection.close()
    else:
        logger.error("Could not get database connection")
        raise Exception("Database connection error")

def fetch_results(query, params=None):
    """Execute a SELECT query and return results as a list of dictionaries"""
    connection = get_connection()
    cursor = None
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            logger.debug(f"Query executed successfully: {query}")
            return results
            
        except Error as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise e
        finally:
            if cursor:
                cursor.close()
            connection.close()
    else:
        logger.error("Could not get database connection")
        raise Exception("Database connection error")
