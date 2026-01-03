/**
 * WAOOAW OAuth Authentication
 * Handles Sign In flow and token management
 */

/**
 * Get backend API URL based on current hostname
 */
function getBackendUrl() {
    const hostname = window.location.hostname;
    
    // Demo environment (Cloud Run URLs)
    if (hostname.includes('waooaw-portal-demo') || hostname.includes('demo-www')) {
        return 'https://waooaw-api-demo-ryvhxvrdna-el.a.run.app';
    }
    // UAT environment (will use Load Balancer)
    else if (hostname.includes('uat-www')) {
        return 'https://uat-api.waooaw.com';
    }
    // Production environment (will use Load Balancer)
    else if (hostname === 'www.waooaw.com') {
        return 'https://api.waooaw.com';
    }
    // Local development
    else {
        return 'http://localhost:8000';
    }
}

/**
 * Initiate OAuth login flow
 */
function handleSignIn() {
    const apiUrl = getBackendUrl();
    window.location.href = `${apiUrl}/auth/login`;
}

/**
 * Handle OAuth callback
 * Called when user returns from Google OAuth
 */
function handleOAuthCallback() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const email = params.get('email');
    const name = params.get('name');
    const picture = params.get('picture');
    const role = params.get('role');
    
    if (token && email) {
        // Store authentication data in localStorage
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_email', email);
        localStorage.setItem('user_name', name || '');
        localStorage.setItem('user_picture', picture || '');
        localStorage.setItem('user_role', role || 'viewer');
        
        console.log('✅ OAuth successful:', { email, role });
        
        // Redirect to marketplace
        window.location.href = '/marketplace.html';
    } else {
        // Handle error
        const error = params.get('error');
        console.error('❌ OAuth failed:', error);
        alert(`Login failed: ${error || 'Unknown error'}`);
        window.location.href = '/';
    }
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('auth_token');
}

/**
 * Get current user info
 */
function getCurrentUser() {
    if (!isAuthenticated()) return null;
    
    return {
        token: localStorage.getItem('auth_token'),
        email: localStorage.getItem('user_email'),
        name: localStorage.getItem('user_name'),
        picture: localStorage.getItem('user_picture'),
        role: localStorage.getItem('user_role'),
    };
}

/**
 * Logout user
 */
function handleSignOut() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_picture');
    localStorage.removeItem('user_role');
    
    window.location.href = '/';
}

/**
 * Update UI based on authentication status
 */
function updateAuthUI() {
    const user = getCurrentUser();
    const signInButtons = document.querySelectorAll('.btn-ghost, button:contains("Sign In")');
    
    if (user) {
        // User is authenticated - show user info
        signInButtons.forEach(btn => {
            if (btn.textContent.includes('Sign In')) {
                btn.textContent = user.email;
                btn.onclick = handleSignOut;
                btn.title = 'Click to sign out';
            }
        });
    } else {
        // User is not authenticated - show Sign In
        signInButtons.forEach(btn => {
            if (!btn.onclick) {
                btn.onclick = handleSignIn;
            }
        });
    }
}

// Auto-detect OAuth callback page
if (window.location.pathname === '/auth/callback' || window.location.search.includes('token=')) {
    handleOAuthCallback();
}

// Update UI on page load
document.addEventListener('DOMContentLoaded', updateAuthUI);
