/**
 * OAuth Callback Handler
 * Processes OAuth redirect from Google
 * Extracts token and redirects to intended page
 */

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import config from '../../config';
import './OAuthCallback.css';

const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);

  useEffect(() => {
    const processCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');
      const state = searchParams.get('state');

      if (error) {
        setStatus('error');
        setError(`Authentication failed: ${error}`);
        setTimeout(() => navigate('/'), 3000);
        return;
      }

      if (!code) {
        setStatus('error');
        setError('No authorization code received');
        setTimeout(() => navigate('/'), 3000);
        return;
      }

      try {
        // Exchange code for token via backend
        const response = await fetch(`${config.apiUrl}/auth/google/callback?code=${code}&state=${state}`);
        
        if (!response.ok) {
          throw new Error('Failed to complete authentication');
        }

        const userData = await response.json();

        // Store auth token
        if (userData.access_token) {
          localStorage.setItem('auth_token', userData.access_token);
          localStorage.setItem('user_email', userData.email);
          localStorage.setItem('user_name', userData.name);
          localStorage.setItem('user_picture', userData.picture);
        }

        setStatus('success');

        // Redirect to original destination or marketplace
        const returnUrl = sessionStorage.getItem('oauth_return_url') || '/marketplace';
        sessionStorage.removeItem('oauth_return_url');
        
        setTimeout(() => navigate(returnUrl), 1000);
      } catch (err) {
        setStatus('error');
        setError(err.message);
        setTimeout(() => navigate('/'), 3000);
      }
    };

    processCallback();
  }, [searchParams, navigate]);

  return (
    <div className="oauth-callback-container">
      <div className="oauth-callback-card">
        {status === 'processing' && (
          <>
            <div className="oauth-spinner"></div>
            <h2>Completing sign in...</h2>
            <p>Please wait while we verify your account</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div className="oauth-success-icon">✓</div>
            <h2>Sign in successful!</h2>
            <p>Redirecting you now...</p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div className="oauth-error-icon">✕</div>
            <h2>Sign in failed</h2>
            <p>{error}</p>
            <p className="oauth-redirect-notice">Redirecting to home...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default OAuthCallback;
