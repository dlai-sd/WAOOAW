import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import config from '../config';
import '../styles/Home.css';
import '../components/GoogleSignIn.css';

function Home() {
  const navigate = useNavigate();
  const [showSignInModal, setShowSignInModal] = useState(false);

  const handleSuccess = async (credentialResponse) => {
    try {
      // Send token to backend
      const response = await fetch(`${config.apiUrl}/auth/google/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credentialResponse.credential }),
      });

      if (!response.ok) throw new Error('Authentication failed');

      const userData = await response.json();

      // Store auth data
      localStorage.setItem('auth_token', userData.access_token);
      localStorage.setItem('user_email', userData.email);
      localStorage.setItem('user_name', userData.name);
      localStorage.setItem('user_picture', userData.picture);

      setShowSignInModal(false);
      navigate('/marketplace');
    } catch (error) {
      alert('Sign in failed: ' + error.message);
    }
  };

  const handleError = () => {
    alert('Sign in failed. Please try again.');
  };

  return (
    <div className="home">
      {/* Sign In Modal */}
      {showSignInModal && (
        <div className="google-signin-modal-overlay" onClick={() => setShowSignInModal(false)}>
          <div className="google-signin-modal" onClick={(e) => e.stopPropagation()}>
            <button className="google-signin-modal-close" onClick={() => setShowSignInModal(false)}>
              ×
            </button>
            <div className="google-signin-modal-header">
              <h2>Sign in to WAOOAW</h2>
              <p>Access your agent marketplace</p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '20px' }}>
              <GoogleLogin onSuccess={handleSuccess} onError={handleError} />
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content fade-in">
            <div className="env-badge">{config.env.toUpperCase()}</div>
            <h1 className="hero-title display">WAOOAW</h1>
            <p className="hero-subtitle">
              The First AI Agent Marketplace That Makes You Say WOW
            </p>
            <p className="hero-tagline">Agents Earn Your Business</p>
            
            <div className="hero-cta">
              <Link to="/marketplace" className="btn btn-primary glow">
                Browse Agents
              </Link>
              <button onClick={() => setShowSignInModal(true)} className="btn btn-secondary">
                Sign In
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
