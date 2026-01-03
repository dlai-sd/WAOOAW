import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import '../styles/AuthCallback.css';

function AuthCallback() {
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function handleCallback() {
      try {
        const params = new URLSearchParams(window.location.search);
        
        // Check if backend sent token directly (our implementation)
        const token = params.get('token');
        const email = params.get('email');
        const name = params.get('name');
        const picture = params.get('picture');
        const role = params.get('role');
        
        if (token && email) {
          // Direct token from backend - store and redirect
          const userData = {
            email,
            name,
            picture,
            role
          };
          
          localStorage.setItem('waooaw_token', token);
          localStorage.setItem('waooaw_user', JSON.stringify(userData));
          
          console.log('✅ OAuth successful:', userData);
          setStatus('success');
          
          // Redirect to marketplace after 1 second
          setTimeout(() => {
            navigate('/marketplace');
          }, 1000);
          
          return;
        }
        
        // Fallback: Check for OAuth code (if backend sends code instead)
        const code = params.get('code');
        const state = params.get('state');
        const error = params.get('error');

        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        if (!code) {
          throw new Error('No token or authorization code received');
        }

        // Exchange code for token via backend
        const response = await fetch(`${config.apiUrl}/auth/callback?code=${code}&state=${state}`, {
          method: 'GET',
          credentials: 'include'
        });

        if (!response.ok) {
          throw new Error('Failed to authenticate');
        }

        const data = await response.json();
        
        // Store token
        localStorage.setItem('waooaw_token', data.access_token);
        localStorage.setItem('waooaw_user', JSON.stringify(data.user));

        setStatus('success');
        
        // Redirect to marketplace after 1 second
        setTimeout(() => {
          navigate('/marketplace');
        }, 1000);

      } catch (err) {
        console.error('Auth callback error:', err);
        setError(err.message);
        setStatus('error');
      }
    }

    handleCallback();
  }, [navigate]);

  return (
    <div className="auth-callback">
      <div className="callback-container">
        {status === 'loading' && (
          <div className="loading">
            <div className="spinner"></div>
            <h2>Authenticating...</h2>
            <p>Please wait while we sign you in</p>
          </div>
        )}
        
        {status === 'success' && (
          <div className="success">
            <div className="success-icon">✓</div>
            <h2>Success!</h2>
            <p>Redirecting to marketplace...</p>
          </div>
        )}
        
        {status === 'error' && (
          <div className="error">
            <div className="error-icon">✕</div>
            <h2>Authentication Failed</h2>
            <p>{error}</p>
            <button onClick={() => navigate('/')}>Return to Home</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default AuthCallback;
