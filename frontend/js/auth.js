/**
 * Authentication Module
 * Handles user authentication, registration, and token management
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set up login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Set up signup form submission
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }

    // Set up logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Check if user is already logged in
    checkAuthStatus();

    // Display current date in dashboard if element exists
    const currentDateElement = document.getElementById('current-date');
    if (currentDateElement) {
        currentDateElement.textContent = formatDate(new Date());
    }
});

/**
 * Handle login form submission
 * @param {Event} e - Form submission event
 */
function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password');
    const errorElement = document.getElementById('login-error');
    
    // Hide any previous errors
    errorElement.classList.add('d-none');
    
    // Validate form
    if (!email || !password.value) {
        showError(errorElement, 'Please enter both email and password');
        return;
    }
    
    // Prepare request data
    const loginData = {
        email: email,
        password: password.value
    };
    
    // Send login request
    fetch('/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            // Store token and user info
            storeAuthData(data.token, data.user);
            
            // Redirect based on role
            redirectBasedOnRole(data.user.role);
        } else {
            showError(errorElement, data.message || 'Login failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        showError(errorElement, 'An error occurred during login. Please try again.');
    });
}

/**
 * Handle signup form submission
 * @param {Event} e - Form submission event
 */
function handleSignup(e) {
    e.preventDefault();
    
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const role = document.getElementById('role').value;
    const errorElement = document.getElementById('signup-error');
    
    // Hide any previous errors
    errorElement.classList.add('d-none');
    
    // Validate form
    if (!email || !password || !confirmPassword) {
        showError(errorElement, 'Please fill in all fields');
        return;
    }
    
    if (password !== confirmPassword) {
        showError(errorElement, 'Passwords do not match');
        return;
    }
    
    if (password.length < 8) {
        showError(errorElement, 'Password must be at least 8 characters long');
        return;
    }
    
    // Prepare request data
    const signupData = {
        email: email,
        password: password,
        role: role
    };
    
    // Send signup request
    fetch('/api/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(signupData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            // Store token and user info
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user_id', data.uid);
            localStorage.setItem('user_role', data.role);
            localStorage.setItem('user_email', email);
            
            // Redirect to complete registration
            window.location.href = `signup.html?role=${data.role}&uid=${data.uid}&token=${data.token}`;
        } else {
            showError(errorElement, data.message || 'Registration failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Signup error:', error);
        showError(errorElement, 'An error occurred during registration. Please try again.');
    });
}

/**
 * Handle user logout
 */
function handleLogout() {
    // Clear authentication data
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
    localStorage.removeItem('patient_id');
    localStorage.removeItem('doctor_id');
    
    // Redirect to login page
    window.location.href = 'index.html';
}

/**
 * Check if user is authenticated and redirect accordingly
 */
function checkAuthStatus() {
    const token = localStorage.getItem('auth_token');
    const role = localStorage.getItem('user_role');
    
    // If not logged in, redirect to login page if not already there
    if (!token) {
        if (!window.location.pathname.includes('index.html') && 
            !window.location.pathname.endsWith('/') && 
            !window.location.pathname.includes('signup.html')) {
            window.location.href = 'index.html';
        }
        return;
    }
    
    // Verify token with backend
    fetch('/api/verify', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Token verification failed');
        }
        return response.json();
    })
    .then(data => {
        // If on index page but already logged in, redirect to dashboard
        if (window.location.pathname.includes('index.html') || 
            window.location.pathname.endsWith('/')) {
            redirectBasedOnRole(role);
        }
        
        // Update user interface with user data if on dashboard
        updateUserInterface(data.user);
    })
    .catch(error => {
        console.error('Auth check error:', error);
        // Clear invalid token
        localStorage.removeItem('auth_token');
        
        // Only redirect if not already on login page
        if (!window.location.pathname.includes('index.html') && 
            !window.location.pathname.endsWith('/')) {
            window.location.href = 'index.html';
        }
    });
}

/**
 * Redirect user based on their role
 * @param {string} role - User role (patient, doctor, admin)
 */
function redirectBasedOnRole(role) {
    switch (role) {
        case 'patient':
            window.location.href = 'dashboard_patient.html';
            break;
        case 'doctor':
            window.location.href = 'dashboard_doctor.html';
            break;
        case 'admin':
            window.location.href = 'dashboard_admin.html';
            break;
        default:
            // Fallback to index if role is unknown
            window.location.href = 'index.html';
    }
}

/**
 * Update user interface with user data
 * @param {Object} user - User data object
 */
function updateUserInterface(user) {
    // Update user name in the sidebar
    const userNameElement = document.getElementById('user-name');
    if (userNameElement && user.name) {
        userNameElement.textContent = user.name;
    } else if (userNameElement) {
        userNameElement.textContent = user.email;
    }
    
    // Store user data for other scripts to use
    localStorage.setItem('user_name', user.name || '');
    localStorage.setItem('user_email', user.email || '');
    
    // If it's a patient, store patient_id
    if (user.patient_id) {
        localStorage.setItem('patient_id', user.patient_id);
    }
    
    // If it's a doctor, store doctor_id
    if (user.doctor_id) {
        localStorage.setItem('doctor_id', user.doctor_id);
    }
}

/**
 * Store authentication data in localStorage
 * @param {string} token - JWT token
 * @param {Object} user - User data object
 */
function storeAuthData(token, user) {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_id', user.uid);
    localStorage.setItem('user_role', user.role);
    localStorage.setItem('user_email', user.email);
    
    if (user.name) {
        localStorage.setItem('user_name', user.name);
    }
    
    if (user.patient_id) {
        localStorage.setItem('patient_id', user.patient_id);
    }
    
    if (user.doctor_id) {
        localStorage.setItem('doctor_id', user.doctor_id);
    }
}

/**
 * Show error message in the specified element
 * @param {HTMLElement} element - Error display element
 * @param {string} message - Error message to display
 */
function showError(element, message) {
    element.textContent = message;
    element.classList.remove('d-none');
}

/**
 * Format date to a readable string
 * @param {Date} date - Date object to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Format datetime for display
 * @param {string} dateTimeStr - Date time string from API
 * @returns {string} Formatted date and time
 */
function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Make authenticated API request
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise} Fetch promise
 */
function apiRequest(url, options = {}) {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        return Promise.reject(new Error('No authentication token found'));
    }
    
    // Set up headers with authentication token
    const headers = options.headers || {};
    headers['Authorization'] = `Bearer ${token}`;
    
    // Return fetch promise with authorization header
    return fetch(url, {
        ...options,
        headers: headers
    });
}

/**
 * Setup sidebar navigation for dashboard pages
 */
document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('content').classList.toggle('active');
        });
    }

    // Handle section navigation
    const sectionLinks = document.querySelectorAll('[data-section]');
    if (sectionLinks.length > 0) {
        sectionLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get target section id
                const targetSection = this.getAttribute('data-section');
                
                // Hide all sections
                document.querySelectorAll('.content-section').forEach(section => {
                    section.classList.remove('active');
                });
                
                // Show target section
                document.getElementById(targetSection).classList.add('active');
                
                // Update active state in sidebar
                document.querySelectorAll('#sidebar .components li').forEach(item => {
                    item.classList.remove('active');
                });
                this.closest('li').classList.add('active');
            });
        });
    }
});
