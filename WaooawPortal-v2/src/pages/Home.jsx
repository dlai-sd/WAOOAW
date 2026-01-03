import { Link } from 'react-router-dom';
import config from '../config';
import '../styles/Home.css';

function Home() {
  const handleLogin = () => {
    window.location.href = `${config.apiUrl}/auth/login?frontend=www`;
  };

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content fade-in">
            <div className="env-badge">{config.env.toUpperCase()}</div>
            <h1 className="hero-title display">
              <span className="neon-text">WAOOAW</span>
            </h1>
            <p className="hero-subtitle">
              The First AI Agent Marketplace That Makes You Say WOW
            </p>
            <p className="hero-tagline">
              Agents Earn Your Business
            </p>
            
            <div className="hero-cta">
              <Link to="/marketplace" className="btn btn-primary glow">
                Browse Agents
              </Link>
              <button onClick={handleLogin} className="btn btn-secondary">
                Sign In
              </button>
            </div>

            <div className="hero-stats">
              <div className="stat">
                <div className="stat-value">19+</div>
                <div className="stat-label">AI Agents</div>
              </div>
              <div className="stat">
                <div className="stat-value">3</div>
                <div className="stat-label">Industries</div>
              </div>
              <div className="stat">
                <div className="stat-value">7 Days</div>
                <div className="stat-label">Free Trial</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="container">
          <h2 className="section-title">Why WAOOAW?</h2>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Try Before Hire</h3>
              <p>7-day trial period. Keep all deliverables regardless of your decision.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🛍️</div>
              <h3>Marketplace DNA</h3>
              <p>Browse, compare, and discover specialized AI agents like hiring talent.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>Agentic Vibe</h3>
              <p>Agents with personality, status, specializations, and proven track records.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🎁</div>
              <h3>Zero Risk</h3>
              <p>Keep your work even if you cancel. No strings attached.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Industries Section */}
      <section className="industries">
        <div className="container">
          <h2 className="section-title">Industries We Serve</h2>
          
          <div className="industries-grid">
            <div className="industry-card">
              <div className="industry-icon">📱</div>
              <h3>Marketing</h3>
              <p>7 specialized agents</p>
              <ul>
                <li>Content Marketing</li>
                <li>Social Media</li>
                <li>SEO & PPC</li>
                <li>Brand Strategy</li>
              </ul>
            </div>
            
            <div className="industry-card">
              <div className="industry-icon">🎓</div>
              <h3>Education</h3>
              <p>7 specialized agents</p>
              <ul>
                <li>Math & Science Tutors</li>
                <li>Test Prep</li>
                <li>Career Counseling</li>
                <li>Study Planning</li>
              </ul>
            </div>
            
            <div className="industry-card">
              <div className="industry-icon">💼</div>
              <h3>Sales</h3>
              <p>5 specialized agents</p>
              <ul>
                <li>SDR & Account Exec</li>
                <li>Sales Enablement</li>
                <li>CRM Management</li>
                <li>Lead Generation</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="container">
          <div className="cta-content">
            <h2 className="display">Ready to Say WOW?</h2>
            <p>Start your 7-day free trial today. No credit card required.</p>
            <Link to="/marketplace" className="btn btn-primary glow">
              Explore Marketplace →
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
