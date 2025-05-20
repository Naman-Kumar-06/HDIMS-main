# Health Data Information Management System (HDIMS)

## Overview

The Health Data Information Management System (HDIMS) is a comprehensive full-stack web application designed to streamline healthcare operations, manage patient information, and optimize doctor-patient interactions. Built with security and scalability in mind, HDIMS provides role-based access control to ensure appropriate data access for administrators, doctors, and patients.

## Features

### For Patients
- **Account Management**: Register, login, and manage personal profiles
- **Appointment Scheduling**: Book, reschedule, and cancel appointments with preferred doctors
- **Medical History**: Access and update personal medical records
- **Doctor Search**: Find specialists based on expertise and availability
- **Health Tracking**: Monitor health metrics and view historical data

### For Doctors
- **Patient Management**: Access patient information, medical history, and treatment plans
- **Appointment Calendar**: View daily/weekly schedules with urgent case prioritization
- **Medical Records**: Create and update patient diagnostic information and prescriptions
- **Performance Analytics**: Track appointment completion rates and patient satisfaction
- **Schedule Management**: Set availability and manage working hours

### For Administrators
- **User Management**: Add, update, and deactivate user accounts
- **System Monitoring**: View system usage metrics and performance statistics
- **Doctor Assignment**: Manage doctor specializations and availability
- **Report Generation**: Create comprehensive reports on hospital operations
- **Data Analytics**: Visualize key performance indicators and resource utilization

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: PostgreSQL for robust data storage
- **ORM**: SQLAlchemy for database operations
- **Authentication**: JWT-based authentication system
- **Frontend**: HTML5, CSS3 (Bootstrap), and JavaScript
- **Data Visualization**: Chart.js for interactive dashboards
- **Deployment**: Supports deployment on any platform with Python and PostgreSQL

## Data Structures & Algorithms

HDIMS implements several custom data structures to optimize healthcare operations:

- **Trie Data Structure**: Efficient patient and disease search with autocomplete functionality
- **Min/Max Heaps**: Priority queuing for appointments and doctor availability optimization
- **Graph Algorithm**: Doctor referral system and disease tracking relationships
- **Segment Tree**: Performance metrics analysis over date ranges

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/hdims.git
   cd hdims
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   - Create a PostgreSQL database
   - Set the environment variables:
     ```bash
     # Windows
     set DATABASE_URL=postgresql://username:password@localhost:5432/hdims_db
     
     # macOS/Linux
     export DATABASE_URL=postgresql://username:password@localhost:5432/hdims_db
     ```

5. **Initialize the database**
   ```bash
   # Start Python shell
   python
   
   # In Python shell
   >>> from main import app, db
   >>> with app.app_context():
   >>>     db.create_all()
   >>> exit()
   ```

6. **Run the development server**
   ```bash
   python main.py
   ```

7. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Default admin login: admin@hdims.com / admin123

## Project Structure

```
hdims/
├── backend/
│   ├── auth/
│   │   └── auth.py                # Authentication logic
│   ├── db/
│   │   └── mysql.py               # Database connection management
│   ├── dsa/
│   │   ├── graph.py               # Doctor referral graph
│   │   ├── maxheap.py             # Doctor availability heap
│   │   ├── minheap.py             # Appointment priority queue
│   │   ├── segment_tree.py        # Performance metrics over time
│   │   └── trie.py                # Search optimization
│   ├── routes/
│   │   ├── admin.py               # Admin API endpoints
│   │   ├── appointments.py        # Appointment API endpoints
│   │   ├── doctors.py             # Doctor API endpoints
│   │   └── patients.py            # Patient API endpoints
│   └── main.py                    # Application entry point
├── frontend/
│   ├── css/
│   │   └── styles.css             # Custom styles
│   ├── js/
│   │   ├── admin.js               # Admin dashboard functionality
│   │   ├── auth.js                # Authentication functionality
│   │   ├── doctor.js              # Doctor dashboard functionality
│   │   └── patient.js             # Patient dashboard functionality
│   ├── dashboard_admin.html       # Admin interface
│   ├── dashboard_doctor.html      # Doctor interface
│   ├── dashboard_patient.html     # Patient interface
│   └── index.html                 # Login page
├── models.py                      # Database models
├── main.py                        # Application configuration
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## API Endpoints

The system provides RESTful API endpoints for all functionality:

### Authentication
- `POST /api/login` - Log in to the system
- `POST /api/signup` - Register a new user
- `GET /api/verify` - Verify authentication token

### Patients
- `GET /api/patients/profile` - Get patient profile
- `PUT /api/patients/profile` - Update patient profile
- `GET /api/patients/medical-history` - Get medical history
- `PUT /api/patients/medical-history` - Update medical history

### Doctors
- `GET /api/doctors/list` - Get all doctors
- `GET /api/doctors/profile` - Get doctor profile
- `PUT /api/doctors/profile` - Update doctor profile
- `GET /api/doctors/availability` - Get doctor availability
- `PUT /api/doctors/availability` - Update doctor availability

### Appointments
- `POST /api/appointments/book` - Book a new appointment
- `GET /api/appointments/list` - List user appointments
- `PUT /api/appointments/cancel/:id` - Cancel an appointment
- `PUT /api/appointments/update/:id` - Update an appointment
- `GET /api/appointments/next` - Get next urgent appointment

### Admin
- `GET /api/admin/report` - Generate analytics report
- `GET /api/admin/users` - Get all users
- `PUT /api/admin/performance` - Update doctor performance metrics

## Security Considerations

- User passwords are securely hashed using Werkzeug's security utilities
- Authentication is handled via JWT tokens
- Role-based access control prevents unauthorized data access
- PostgreSQL provides robust data storage with transaction support
- Input validation is performed on all API endpoints

## Future Enhancements

- Real-time notifications using WebSockets
- Integration with telemedicine services
- Mobile application for iOS and Android
- AI-powered diagnosis assistance
- Integration with wearable health devices
- Data export functionality for regulatory compliance

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Bootstrap for responsive UI components
- Chart.js for interactive data visualization
- Flask for the lightweight web framework
- SQLAlchemy for database ORM
- PostgreSQL for robust data storage