// frontend/static/js/auth.js
const API_BASE_URL = window.location.origin + '/api';

console.log('✅ auth.js loaded!');

function showError(message) {
    console.log('❌ Error:', message);
    const el = document.getElementById('errorMessage');
    if (el) {
        el.textContent = message;
        el.className = 'error-message show';
    }
}

function showSuccess(message) {
    console.log('✅ Success:', message);
    const el = document.getElementById('successMessage');
    if (el) {
        el.textContent = message;
        el.className = 'success-message show';
    }
}

function hideMessages() {
    const error = document.getElementById('errorMessage');
    const success = document.getElementById('successMessage');
    if (error) error.className = 'error-message';
    if (success) success.className = 'success-message';
}

// ===== SIGNUP =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM loaded!');
    
    const signupForm = document.getElementById('signupForm');
    console.log('Signup form found:', !!signupForm);
    
    if (signupForm) {
        signupForm.addEventListener('submit', async function(e) {
            console.log('✅ Form submitted!');
            e.preventDefault();  // ✅ THIS IS CRITICAL - prevents GET request
            hideMessages();
            
            const fullName = document.getElementById('fullName').value.trim();
            const username = document.getElementById('username').value.trim().toLowerCase();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const terms = document.getElementById('terms').checked;
            
            console.log('Form data:', { fullName, username, email, password, confirmPassword, terms });
            
            // Validation
            if (!username || !email || !password || !confirmPassword) {
                showError('Please fill in all required fields');
                return;
            }
            if (username.length < 3) {
                showError('Username must be at least 3 characters');
                return;
            }
            if (password !== confirmPassword) {
                showError('Passwords do not match');
                return;
            }
            if (!terms) {
                showError('Please agree to the Terms of Service');
                return;
            }
            
            const btn = document.getElementById('signupBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
            
            try {
                console.log('Sending signup request...');
                const response = await fetch(`${API_BASE_URL}/auth/signup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        full_name: fullName || undefined, 
                        username, 
                        email, 
                        password 
                    })
                });
                
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Signup failed');
                }
                
                showSuccess('Account created! Redirecting to login...');
                setTimeout(() => window.location.href = '/login', 2000);
                
            } catch (error) {
                console.error('Signup error:', error);
                showError(error.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
            }
        });
    }
});

// ===== LOGIN =====
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    console.log('Login form found:', !!loginForm);
    
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            hideMessages();
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                showError('Please fill in all fields');
                return;
            }
            
            const btn = document.getElementById('loginBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';
            
            try {
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Login failed');
                
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                
                window.location.href = '/dashboard';
            } catch (error) {
                showError(error.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
            }
        });
    }
});