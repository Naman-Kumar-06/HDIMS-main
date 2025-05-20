/**
 * Patient Dashboard JavaScript
 * Handles patient-specific functionality and interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializePatientDashboard();

    // Set up event listeners for patient dashboard
    setupPatientEventListeners();

    // Simulate some health data for the chart
    createHealthMetricsChart();
});

/**
 * Initialize the patient dashboard with data
 */
function initializePatientDashboard() {
    // Load appointment data
    loadPatientAppointments();

    // Load available doctors
    loadAvailableDoctors();

    // Load patient profile
    loadPatientProfile();

    // Load medical history
    loadMedicalHistory();

    // Update dashboard counters
    updateDashboardCounters();
}

/**
 * Set up event listeners for interactions on the patient dashboard
 */
function setupPatientEventListeners() {
    // New appointment button
    const newAppointmentBtn = document.getElementById('new-appointment-btn');
    if (newAppointmentBtn) {
        newAppointmentBtn.addEventListener('click', showAppointmentForm);
    }

    // Cancel appointment button
    const cancelAppointmentBtn = document.getElementById('cancel-appointment-btn');
    if (cancelAppointmentBtn) {
        cancelAppointmentBtn.addEventListener('click', hideAppointmentForm);
    }

    // Appointment form submission
    const appointmentForm = document.getElementById('appointment-form');
    if (appointmentForm) {
        appointmentForm.addEventListener('submit', bookAppointment);
    }

    // Find available doctors button
    const findDoctorsBtn = document.getElementById('find-available-doctors');
    if (findDoctorsBtn) {
        findDoctorsBtn.addEventListener('click', loadAvailableDoctors);
    }

    // Edit medical history button
    const editHistoryBtn = document.getElementById('edit-history-btn');
    if (editHistoryBtn) {
        editHistoryBtn.addEventListener('click', toggleHistoryEdit);
    }

    // Save medical history button
    const saveHistoryBtn = document.getElementById('save-history-btn');
    if (saveHistoryBtn) {
        saveHistoryBtn.addEventListener('click', saveMedicalHistory);
    }

    // Cancel history edit button
    const cancelHistoryBtn = document.getElementById('cancel-history-btn');
    if (cancelHistoryBtn) {
        cancelHistoryBtn.addEventListener('click', cancelHistoryEdit);
    }

    // Profile form submission
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', updatePatientProfile);
    }

    // Password change form submission
    const passwordForm = document.getElementById('password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', changePassword);
    }
}

/**
 * Load patient appointments from the API
 */
function loadPatientAppointments() {
    apiRequest('/api/appointments/list')
        .then(response => response.json())
        .then(data => {
            if (data.appointments) {
                // Process appointments
                const appointments = data.appointments;
                
                // Separate appointments by status
                const upcoming = appointments.filter(app => app.status === 'scheduled');
                const past = appointments.filter(app => app.status === 'completed');
                const cancelled = appointments.filter(app => app.status === 'cancelled');
                
                // Update appointment count
                document.getElementById('appointment-count').textContent = upcoming.length;
                
                // Populate upcoming appointments table
                populateAppointmentsTable('upcoming-appointments', upcoming);
                
                // Populate past appointments table
                populateAppointmentsTable('past-appointments', past, false);
                
                // Populate cancelled appointments table
                populateAppointmentsTable('cancelled-appointments', cancelled, true, true);
                
                // Populate next appointment on dashboard
                if (upcoming.length > 0) {
                    // Sort by date
                    upcoming.sort((a, b) => new Date(a.appointment_time) - new Date(b.appointment_time));
                    const nextAppointment = upcoming[0];
                    populateNextAppointment(nextAppointment);
                } else {
                    document.getElementById('next-appointment-container').innerHTML = 
                        '<div class="alert alert-info">No upcoming appointments scheduled.</div>';
                }
                
                // Populate recent activity
                populateRecentActivity(appointments);
            }
        })
        .catch(error => {
            console.error('Error loading appointments:', error);
            showErrorAlert('appointments-section', 'Failed to load appointments. Please try again later.');
        });
}

/**
 * Populate appointments table with data
 * @param {string} tableId - ID of the table to populate
 * @param {Array} appointments - Array of appointment objects
 * @param {boolean} showActions - Whether to show action buttons
 * @param {boolean} isCancelled - Whether these are cancelled appointments
 */
function populateAppointmentsTable(tableId, appointments, showActions = true, isCancelled = false) {
    const tableBody = document.getElementById(tableId);
    
    if (!tableBody) return;
    
    if (appointments.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="${showActions ? 6 : 5}" class="text-center">No appointments found.</td></tr>`;
        return;
    }
    
    let html = '';
    
    appointments.forEach(appointment => {
        html += `<tr>
            <td>${formatDateTime(appointment.appointment_time)}</td>
            <td>${appointment.doctor_name || 'N/A'}</td>
            <td>${appointment.specialization || 'N/A'}</td>
            <td>${appointment.reason || 'N/A'}</td>`;
            
        if (!isCancelled) {
            html += `<td><span class="badge ${getStatusBadgeClass(appointment.status)}">${appointment.status}</span></td>`;
        }
        
        if (showActions) {
            html += `<td>`;
            
            if (!isCancelled && appointment.status === 'scheduled') {
                html += `<button class="btn btn-sm btn-danger cancel-appointment" data-id="${appointment.id}">
                    <i class="fas fa-times-circle"></i> Cancel
                </button>`;
            } else if (isCancelled) {
                html += `<button class="btn btn-sm btn-primary rebook-appointment" data-doctor="${appointment.doctor_id}" data-reason="${appointment.reason}">
                    <i class="fas fa-redo"></i> Rebook
                </button>`;
            }
            
            html += `</td>`;
        }
        
        html += `</tr>`;
    });
    
    tableBody.innerHTML = html;
    
    // Add event listeners to cancel buttons
    const cancelButtons = tableBody.querySelectorAll('.cancel-appointment');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const appointmentId = this.getAttribute('data-id');
            cancelAppointment(appointmentId);
        });
    });
    
    // Add event listeners to rebook buttons
    const rebookButtons = tableBody.querySelectorAll('.rebook-appointment');
    rebookButtons.forEach(button => {
        button.addEventListener('click', function() {
            const doctorId = this.getAttribute('data-doctor');
            const reason = this.getAttribute('data-reason');
            showAppointmentForm();
            
            // Pre-fill the form
            document.getElementById('doctor-select').value = doctorId;
            document.getElementById('appointment-reason').value = reason;
        });
    });
}

/**
 * Get the appropriate Bootstrap badge class for appointment status
 * @param {string} status - Appointment status
 * @returns {string} - Badge class
 */
function getStatusBadgeClass(status) {
    switch (status) {
        case 'scheduled':
            return 'bg-primary';
        case 'completed':
            return 'bg-success';
        case 'cancelled':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

/**
 * Populate next appointment card on the dashboard
 * @param {Object} appointment - Next appointment object
 */
function populateNextAppointment(appointment) {
    const container = document.getElementById('next-appointment-container');
    if (!container) return;
    
    const formattedDate = formatDateTime(appointment.appointment_time);
    
    const html = `
        <div class="d-flex align-items-center mb-3">
            <div class="flex-shrink-0">
                <div class="bg-primary text-white rounded-circle p-3">
                    <i class="fas fa-calendar-check fa-2x"></i>
                </div>
            </div>
            <div class="flex-grow-1 ms-3">
                <h5 class="mb-1">Dr. ${appointment.doctor_name}</h5>
                <p class="mb-0 text-muted">${appointment.specialization}</p>
            </div>
        </div>
        <div class="mb-3">
            <div class="d-flex justify-content-between">
                <span><i class="fas fa-clock me-2"></i>Date & Time:</span>
                <span class="text-primary">${formattedDate}</span>
            </div>
            <div class="d-flex justify-content-between mt-2">
                <span><i class="fas fa-info-circle me-2"></i>Reason:</span>
                <span>${appointment.reason}</span>
            </div>
            <div class="d-flex justify-content-between mt-2">
                <span><i class="fas fa-exclamation-triangle me-2"></i>Urgency:</span>
                <span>${getUrgencyLabel(appointment.urgency)}</span>
            </div>
        </div>
        <div class="d-grid">
            <button class="btn btn-danger cancel-next-appointment" data-id="${appointment.id}">
                <i class="fas fa-times-circle me-2"></i>Cancel Appointment
            </button>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Add event listener to cancel button
    const cancelButton = container.querySelector('.cancel-next-appointment');
    if (cancelButton) {
        cancelButton.addEventListener('click', function() {
            const appointmentId = this.getAttribute('data-id');
            cancelAppointment(appointmentId);
        });
    }
}

/**
 * Get user-friendly label for urgency level
 * @param {number} urgency - Urgency level (0-3)
 * @returns {string} - Urgency label
 */
function getUrgencyLabel(urgency) {
    const levels = [
        'Regular Checkup',
        'Minor Issue',
        'Concerning Issue',
        'Urgent Care Needed'
    ];
    
    return levels[urgency] || 'Unknown';
}

/**
 * Populate recent activity section on dashboard
 * @param {Array} appointments - All appointments
 */
function populateRecentActivity(appointments) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    // Sort appointments by date (most recent first)
    appointments.sort((a, b) => new Date(b.appointment_time) - new Date(a.appointment_time));
    
    // Take the most recent 5 activities
    const recentActivities = appointments.slice(0, 5);
    
    if (recentActivities.length === 0) {
        container.innerHTML = '<li class="timeline-item">No recent activity.</li>';
        return;
    }
    
    let html = '';
    
    recentActivities.forEach(activity => {
        const date = new Date(activity.appointment_time);
        const formattedDate = date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
        });
        
        const statusClass = {
            'scheduled': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        }[activity.status] || 'secondary';
        
        html += `
            <li class="timeline-item">
                <div class="timeline-marker bg-${statusClass}"></div>
                <div class="timeline-content">
                    <h6 class="mb-0">${activity.status === 'completed' ? 'Visited' : activity.status === 'cancelled' ? 'Cancelled appointment with' : 'Booked appointment with'} Dr. ${activity.doctor_name}</h6>
                    <small class="text-muted">${formattedDate} - ${activity.specialization}</small>
                    <p class="mb-0">${activity.reason}</p>
                </div>
            </li>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Show appointment booking form
 */
function showAppointmentForm() {
    document.getElementById('appointment-form').classList.remove('d-none');
}

/**
 * Hide appointment booking form
 */
function hideAppointmentForm() {
    document.getElementById('appointment-form').classList.add('d-none');
}

/**
 * Book a new appointment
 * @param {Event} e - Form submission event
 */
function bookAppointment(e) {
    e.preventDefault();
    
    const doctorId = document.getElementById('doctor-select').value;
    const appointmentDate = document.getElementById('appointment-date').value;
    const reason = document.getElementById('appointment-reason').value;
    const urgency = document.getElementById('appointment-urgency').value;
    
    if (!doctorId || !appointmentDate || !reason) {
        alert('Please fill in all required fields.');
        return;
    }
    
    const appointmentData = {
        doctor_id: doctorId,
        appointment_time: appointmentDate,
        reason: reason,
        urgency: parseInt(urgency, 10)
    };
    
    apiRequest('/api/appointments/book', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(appointmentData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message && data.message.includes('successfully')) {
            alert('Appointment booked successfully!');
            hideAppointmentForm();
            
            // Reset form
            document.getElementById('appointment-form').reset();
            
            // Reload appointments
            loadPatientAppointments();
            updateDashboardCounters();
        } else {
            alert(data.message || 'Failed to book appointment. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error booking appointment:', error);
        alert('An error occurred while booking the appointment. Please try again later.');
    });
}

/**
 * Cancel an existing appointment
 * @param {number} appointmentId - ID of the appointment to cancel
 */
function cancelAppointment(appointmentId) {
    if (!confirm('Are you sure you want to cancel this appointment?')) {
        return;
    }
    
    apiRequest(`/api/appointments/cancel/${appointmentId}`, {
        method: 'PUT'
    })
    .then(response => response.json())
    .then(data => {
        if (data.message && data.message.includes('successfully')) {
            alert('Appointment cancelled successfully!');
            
            // Reload appointments
            loadPatientAppointments();
            updateDashboardCounters();
        } else {
            alert(data.message || 'Failed to cancel appointment. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error cancelling appointment:', error);
        alert('An error occurred while cancelling the appointment. Please try again later.');
    });
}

/**
 * Load available doctors for appointments
 */
function loadAvailableDoctors() {
    const specialization = document.getElementById('specialty-filter')?.value || '';
    const queryParams = specialization ? `?specialization=${specialization}` : '';
    
    // Load doctors for appointment booking dropdown
    apiRequest(`/api/doctors/available${queryParams}`)
        .then(response => response.json())
        .then(data => {
            if (data.doctors) {
                // Populate doctor select dropdown
                const doctorSelect = document.getElementById('doctor-select');
                if (doctorSelect) {
                    let options = '<option value="" selected disabled>Choose a doctor</option>';
                    
                    data.doctors.forEach(doctor => {
                        options += `<option value="${doctor.doctor_id}">${doctor.name} (${doctor.specialization})</option>`;
                    });
                    
                    doctorSelect.innerHTML = options;
                }
                
                // Populate doctors in the doctors section
                populateAvailableDoctors(data.doctors);
                
                // Update doctor count
                document.getElementById('doctors-count').textContent = data.doctors.length;
            }
        })
        .catch(error => {
            console.error('Error loading doctors:', error);
            showErrorAlert('doctors-section', 'Failed to load available doctors. Please try again later.');
        });
}

/**
 * Populate available doctors in the doctors section
 * @param {Array} doctors - Array of doctor objects
 */
function populateAvailableDoctors(doctors) {
    const container = document.getElementById('doctors-container');
    if (!container) return;
    
    if (doctors.length === 0) {
        container.innerHTML = '<div class="col-12 text-center py-4"><div class="alert alert-info">No doctors found matching your criteria.</div></div>';
        return;
    }
    
    let html = '';
    
    doctors.forEach(doctor => {
        html += `
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">Dr. ${doctor.name}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">${doctor.specialization}</h6>
                        <p class="card-text small">
                            <i class="fas fa-calendar-alt me-1"></i> ${doctor.availability}
                        </p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-success">Available</span>
                            <div>
                                <button class="btn btn-sm btn-outline-primary view-doctor" data-id="${doctor.doctor_id}">
                                    <i class="fas fa-eye me-1"></i> Details
                                </button>
                                <button class="btn btn-sm btn-primary book-with-doctor" data-id="${doctor.doctor_id}">
                                    <i class="fas fa-calendar-plus me-1"></i> Book
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Add event listeners to buttons
    const viewButtons = container.querySelectorAll('.view-doctor');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const doctorId = this.getAttribute('data-id');
            viewDoctorDetails(doctorId);
        });
    });
    
    const bookButtons = container.querySelectorAll('.book-with-doctor');
    bookButtons.forEach(button => {
        button.addEventListener('click', function() {
            const doctorId = this.getAttribute('data-id');
            document.getElementById('doctor-select').value = doctorId;
            showAppointmentForm();
            
            // Scroll to appointments section
            document.querySelector('[href="#appointments-section"]').click();
        });
    });
}

/**
 * View doctor details in a modal
 * @param {number} doctorId - ID of the doctor to view
 */
function viewDoctorDetails(doctorId) {
    const modal = new bootstrap.Modal(document.getElementById('doctorDetailsModal'));
    const content = document.getElementById('doctor-details-content');
    
    // Show loading state
    content.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Loading doctor details...</p>
        </div>
    `;
    
    modal.show();
    
    // Fetch doctor details
    apiRequest(`/api/doctors/detail/${doctorId}`)
        .then(response => response.json())
        .then(data => {
            if (data.doctor) {
                const doctor = data.doctor;
                const performance = data.performance || { avg_response_time: 0, avg_satisfaction: 0 };
                
                content.innerHTML = `
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <img src="https://pixabay.com/get/g05361694495e5571ff9dc79e74383ea2f262519fba95b1d2b8523dea6da37211db6c28afc7e3c520b8dc607fd972d6e2cbc2551f3ab0c00f6a8ab13ab9a9fe7c_1280.jpg" 
                                 class="img-thumbnail rounded-circle mb-3" 
                                 alt="Dr. ${doctor.name}" 
                                 style="width: 150px; height: 150px; object-fit: cover;">
                            <h5>Dr. ${doctor.name}</h5>
                            <p class="badge bg-primary">${doctor.specialization}</p>
                        </div>
                        <div class="col-md-8">
                            <h5 class="border-bottom pb-2">Doctor Information</h5>
                            <div class="mb-3">
                                <p><strong><i class="fas fa-phone me-2"></i>Contact:</strong> ${doctor.contact || 'N/A'}</p>
                                <p><strong><i class="fas fa-calendar-alt me-2"></i>Availability:</strong> ${doctor.availability || 'N/A'}</p>
                            </div>
                            
                            <h5 class="border-bottom pb-2">Performance Metrics</h5>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card mb-2">
                                        <div class="card-body py-2 px-3">
                                            <div class="d-flex justify-content-between align-items-center">
                                                <span>Avg. Response Time:</span>
                                                <span>${performance.avg_response_time.toFixed(1)} min</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card mb-2">
                                        <div class="card-body py-2 px-3">
                                            <div class="d-flex justify-content-between align-items-center">
                                                <span>Satisfaction Score:</span>
                                                <span>${performance.avg_satisfaction.toFixed(1)} / 5</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Set up the book button
                const bookBtn = document.getElementById('book-with-doctor-btn');
                bookBtn.setAttribute('data-id', doctor.doctor_id);
                bookBtn.addEventListener('click', function() {
                    const doctorId = this.getAttribute('data-id');
                    document.getElementById('doctor-select').value = doctorId;
                    modal.hide();
                    showAppointmentForm();
                    
                    // Scroll to appointments section
                    document.querySelector('[href="#appointments-section"]').click();
                });
            } else {
                content.innerHTML = '<div class="alert alert-danger">Failed to load doctor details.</div>';
            }
        })
        .catch(error => {
            console.error('Error loading doctor details:', error);
            content.innerHTML = '<div class="alert alert-danger">An error occurred while loading doctor details.</div>';
        });
}

/**
 * Load patient profile information
 */
function loadPatientProfile() {
    const patientId = localStorage.getItem('patient_id');
    
    if (!patientId) {
        console.error('Patient ID not found in localStorage');
        return;
    }
    
    apiRequest(`/api/patients/detail/${patientId}`)
        .then(response => response.json())
        .then(data => {
            if (data.patient) {
                const patient = data.patient;
                
                // Update profile display
                document.getElementById('profile-name').textContent = patient.name;
                document.getElementById('profile-email').textContent = localStorage.getItem('user_email') || '';
                
                // Update user name in sidebar
                document.getElementById('user-name').textContent = patient.name;
                
                // Update form fields
                document.getElementById('profile-full-name').value = patient.name;
                document.getElementById('profile-dob').value = patient.dob;
                document.getElementById('profile-gender').value = patient.gender;
                document.getElementById('profile-contact').value = patient.contact;
                document.getElementById('profile-address').value = patient.address;
            }
        })
        .catch(error => {
            console.error('Error loading patient profile:', error);
            showErrorAlert('profile-section', 'Failed to load profile information. Please try again later.');
        });
}

/**
 * Update patient profile information
 * @param {Event} e - Form submission event
 */
function updatePatientProfile(e) {
    e.preventDefault();
    
    const patientId = localStorage.getItem('patient_id');
    
    if (!patientId) {
        alert('Patient ID not found. Please log in again.');
        return;
    }
    
    const profileData = {
        name: document.getElementById('profile-full-name').value,
        dob: document.getElementById('profile-dob').value,
        gender: document.getElementById('profile-gender').value,
        contact: document.getElementById('profile-contact').value,
        address: document.getElementById('profile-address').value
    };
    
    apiRequest(`/api/patients/update/${patientId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message && data.message.includes('successfully')) {
            alert('Profile updated successfully!');
            
            // Update displayed information
            document.getElementById('profile-name').textContent = profileData.name;
            document.getElementById('user-name').textContent = profileData.name;
            
            // Store updated name
            localStorage.setItem('user_name', profileData.name);
        } else {
            alert(data.message || 'Failed to update profile. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error updating profile:', error);
        alert('An error occurred while updating your profile. Please try again later.');
    });
}

/**
 * Change user password
 * @param {Event} e - Form submission event
 */
function changePassword(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-new-password').value;
    
    if (!currentPassword || !newPassword || !confirmPassword) {
        alert('Please fill in all password fields.');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        alert('New passwords do not match.');
        return;
    }
    
    if (newPassword.length < 8) {
        alert('New password must be at least 8 characters long.');
        return;
    }
    
    // In a real implementation, we would make an API call to change the password
    // This is a simplified version for the demo
    alert('Password change functionality would be implemented here.');
    document.getElementById('password-form').reset();
}

/**
 * Load patient's medical history
 */
function loadMedicalHistory() {
    const patientId = localStorage.getItem('patient_id');
    
    if (!patientId) {
        console.error('Patient ID not found in localStorage');
        return;
    }
    
    apiRequest(`/api/patients/detail/${patientId}`)
        .then(response => response.json())
        .then(data => {
            if (data.patient) {
                const patient = data.patient;
                
                // Update medical history display
                const historyDisplay = document.getElementById('history-display');
                const historyText = document.getElementById('medical-history-text');
                
                if (patient.history && patient.history.trim() !== '') {
                    historyDisplay.innerHTML = formatMedicalHistory(patient.history);
                    historyText.value = patient.history;
                } else {
                    historyDisplay.innerHTML = '<p class="text-muted">No medical history recorded. Click "Edit" to add your medical history.</p>';
                    historyText.value = '';
                }
                
                // Populate past conditions and medications (for demo purposes)
                populateMockMedicalData();
                
                // Populate visit history from appointments
                populateVisitHistory(data.appointments || []);
            }
        })
        .catch(error => {
            console.error('Error loading medical history:', error);
            showErrorAlert('medical-history-section', 'Failed to load medical history. Please try again later.');
        });
}

/**
 * Format medical history text with proper HTML paragraphs
 * @param {string} history - Raw medical history text
 * @returns {string} - Formatted HTML
 */
function formatMedicalHistory(history) {
    if (!history) return '<p class="text-muted">No medical history recorded.</p>';
    
    // Split by line breaks and wrap in paragraphs
    return history.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => `<p>${line}</p>`)
        .join('');
}

/**
 * Populate mock medical data for demonstration
 */
function populateMockMedicalData() {
    // This is for demonstration only - in a real app, this would come from the API
    const pastConditions = [
        'Common Cold (2022)',
        'Seasonal Allergies (2021-Present)',
        'Sprained Ankle (2020)'
    ];
    
    const medications = [
        'Vitamin D - 1000 IU Daily',
        'Loratadine - 10mg As needed for allergies',
        'Ibuprofen - 400mg As needed for pain'
    ];
    
    const conditionsList = document.getElementById('past-conditions');
    const medicationsList = document.getElementById('medications-list');
    
    if (conditionsList) {
        conditionsList.innerHTML = pastConditions.length > 0 
            ? pastConditions.map(condition => `<li class="list-group-item">${condition}</li>`).join('')
            : '<li class="list-group-item">No past conditions recorded.</li>';
    }
    
    if (medicationsList) {
        medicationsList.innerHTML = medications.length > 0
            ? medications.map(med => `<li class="list-group-item">${med}</li>`).join('')
            : '<li class="list-group-item">No medications recorded.</li>';
    }
}

/**
 * Populate visit history table from appointments
 * @param {Array} appointments - Array of appointment objects
 */
function populateVisitHistory(appointments) {
    const tableBody = document.getElementById('visit-history');
    if (!tableBody) return;
    
    // Filter only completed appointments
    const completedVisits = appointments.filter(app => app.status === 'completed');
    
    if (completedVisits.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No visit history found.</td></tr>';
        return;
    }
    
    // Sort by date (most recent first)
    completedVisits.sort((a, b) => new Date(b.appointment_time) - new Date(a.appointment_time));
    
    let html = '';
    
    completedVisits.forEach(visit => {
        const date = new Date(visit.appointment_time);
        const formattedDate = date.toLocaleDateString('en-US', { 
            year: 'numeric',
            month: 'short', 
            day: 'numeric' 
        });
        
        html += `<tr>
            <td>${formattedDate}</td>
            <td>Dr. ${visit.doctor_name} (${visit.specialization})</td>
            <td>${visit.reason || 'N/A'}</td>
            <td>${visit.diagnosis || 'Not recorded'}</td>
            <td>${visit.prescription || 'None prescribed'}</td>
        </tr>`;
    });
    
    tableBody.innerHTML = html;
}

/**
 * Toggle medical history edit mode
 */
function toggleHistoryEdit() {
    document.getElementById('history-display').classList.add('d-none');
    document.getElementById('history-edit').classList.remove('d-none');
}

/**
 * Save updated medical history
 */
function saveMedicalHistory() {
    const patientId = localStorage.getItem('patient_id');
    const history = document.getElementById('medical-history-text').value;
    
    if (!patientId) {
        alert('Patient ID not found. Please log in again.');
        return;
    }
    
    apiRequest(`/api/patients/update/${patientId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ history: history })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message && data.message.includes('successfully')) {
            // Update display
            document.getElementById('history-display').innerHTML = formatMedicalHistory(history);
            
            // Hide edit form
            cancelHistoryEdit();
        } else {
            alert(data.message || 'Failed to update medical history. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error updating medical history:', error);
        alert('An error occurred while updating your medical history. Please try again later.');
    });
}

/**
 * Cancel history edit mode
 */
function cancelHistoryEdit() {
    document.getElementById('history-display').classList.remove('d-none');
    document.getElementById('history-edit').classList.add('d-none');
}

/**
 * Update dashboard counters
 */
function updateDashboardCounters() {
    // This function would normally make API calls to get the latest counts
    // For simplicity, we'll just reuse the counts from the data we already loaded
}

/**
 * Create health metrics chart for demonstration
 */
function createHealthMetricsChart() {
    const ctx = document.getElementById('healthMetricsChart');
    if (!ctx) return;
    
    // Sample data for demonstration
    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    
    const data = {
        labels: labels,
        datasets: [
            {
                label: 'Blood Pressure (Systolic)',
                data: [120, 118, 125, 122, 119, 121],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.3
            },
            {
                label: 'Blood Pressure (Diastolic)',
                data: [80, 78, 82, 79, 77, 80],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                tension: 0.3
            },
            {
                label: 'Heart Rate (bpm)',
                data: [72, 74, 70, 71, 73, 72],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.3
            }
        ]
    };
    
    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Health Metrics (Last 6 Months)'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 60
                }
            }
        }
    };
    
    new Chart(ctx, config);
}

/**
 * Show error alert in a specific section
 * @param {string} sectionId - ID of the section to show the alert in
 * @param {string} message - Error message to display
 */
function showErrorAlert(sectionId, message) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.role = 'alert';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at the top of the section
    section.insertBefore(alertDiv, section.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
        alert.close();
    }, 5000);
}
