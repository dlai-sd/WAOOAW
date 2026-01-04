import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../config';
import '../styles/Marketplace.css';

function Marketplace() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [filters, setFilters] = useState({
    industry: 'all',
    search: ''
  });
  const navigate = useNavigate();

  useEffect(() => {
    // Load auth state from storage on first render
    const token = localStorage.getItem('auth_token');
    if (token) {
      setUser({
        token,
        email: localStorage.getItem('user_email') || '',
        name: localStorage.getItem('user_name') || 'Signed in',
        picture: localStorage.getItem('user_picture') || '',
      });
    }

    // Mock agents data (will be replaced with API call)
    const mockAgents = [
      {
        id: 1,
        name: 'Content Marketing Agent',
        industry: 'marketing',
        specialty: 'Healthcare',
        rating: 4.9,
        status: 'available',
        avatar: 'CM',
        price: '₹12,000/month',
        activity: 'Posted 23 times today',
        retention: '98%'
      },
      {
        id: 2,
        name: 'Math Tutor Agent',
        industry: 'education',
        specialty: 'JEE/NEET',
        rating: 4.8,
        status: 'working',
        avatar: 'MT',
        price: '₹8,000/month',
        activity: '5 sessions today',
        retention: '95%'
      },
      {
        id: 3,
        name: 'SDR Agent',
        industry: 'sales',
        specialty: 'B2B SaaS',
        rating: 5.0,
        status: 'available',
        avatar: 'SDR',
        price: '₹15,000/month',
        activity: '12 leads generated',
        retention: '99%'
      }
    ];

    setTimeout(() => {
      setAgents(mockAgents);
      setLoading(false);
    }, 500);
  }, []);

  const filteredAgents = agents.filter(agent => {
    const matchesIndustry = filters.industry === 'all' || agent.industry === filters.industry;
    const matchesSearch = agent.name.toLowerCase().includes(filters.search.toLowerCase()) ||
                         agent.specialty.toLowerCase().includes(filters.search.toLowerCase());
    return matchesIndustry && matchesSearch;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'available': return 'var(--color-green)';
      case 'working': return 'var(--color-yellow)';
      case 'offline': return 'var(--color-red)';
      default: return 'var(--color-gray-400)';
    }
  };

  const handleStartTrial = (agentId) => {
    if (!user?.token) {
      // If not signed in, send them home to sign in cleanly
      navigate('/');
      return;
    }

    // Start trial logic placeholder
    console.log('Starting trial for agent:', agentId);
  };

  const handleLogout = () => {
    const email = localStorage.getItem('user_email');

    // Clear local and session storage auth artefacts
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_picture');
    sessionStorage.removeItem('oauth_return_url');

    // Revoke Google session if available for a clean sign-out
    if (window.google?.accounts?.id?.revoke && email) {
      window.google.accounts.id.revoke(email, () => {});
    }

    setUser(null);
    navigate('/');
  };

  return (
    <div className="marketplace">
      <div className="container">
        {/* User bar */}
        <div className="user-bar">
          <div className="user-identity">
            {user?.picture ? (
              <img src={user.picture} alt="User avatar" className="user-avatar" />
            ) : (
              <div className="user-avatar fallback">{(user?.name || 'Guest').slice(0, 2).toUpperCase()}</div>
            )}
            <div>
              <div className="user-name">{user?.name || 'Guest'}</div>
              <div className="user-email">{user?.email || 'Not signed in'}</div>
            </div>
          </div>
          <div className="user-actions">
            {user ? (
              <button className="btn btn-secondary" onClick={handleLogout}>Logout</button>
            ) : (
              <button className="btn btn-primary" onClick={() => navigate('/')}>Sign In</button>
            )}
          </div>
        </div>

        {/* Header */}
        <div className="marketplace-header">
          <div className="env-badge">{config.env.toUpperCase()}</div>
          <h1 className="display">
            <span className="neon-text">WAOOAW</span> Marketplace
          </h1>
          <p>Browse specialized AI agents across Marketing, Education, and Sales</p>
        </div>

        {/* Search and Filters */}
        <div className="marketplace-filters">
          <input
            type="text"
            placeholder="Search agents by name or specialty..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="search-input"
          />
          
          <div className="filter-buttons">
            <button
              className={filters.industry === 'all' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilters({ ...filters, industry: 'all' })}
            >
              All
            </button>
            <button
              className={filters.industry === 'marketing' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilters({ ...filters, industry: 'marketing' })}
            >
              Marketing
            </button>
            <button
              className={filters.industry === 'education' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilters({ ...filters, industry: 'education' })}
            >
              Education
            </button>
            <button
              className={filters.industry === 'sales' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => setFilters({ ...filters, industry: 'sales' })}
            >
              Sales
            </button>
          </div>
        </div>

        {/* Agents Grid */}
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading agents...</p>
          </div>
        ) : (
          <div className="agents-grid">
            {filteredAgents.map(agent => (
              <div key={agent.id} className="agent-card">
                <div className="agent-header">
                  <div className="agent-avatar" style={{
                    background: `linear-gradient(135deg, var(--color-cyan), var(--color-purple))`
                  }}>
                    {agent.avatar}
                  </div>
                  <div className="agent-status">
                    <span 
                      className="status-dot" 
                      style={{ backgroundColor: getStatusColor(agent.status) }}
                    ></span>
                    <span className="status-text">{agent.status}</span>
                  </div>
                </div>
                
                <div className="agent-info">
                  <h3>{agent.name}</h3>
                  <p className="agent-specialty">
                    <span className="specialty-badge">{agent.specialty}</span>
                  </p>
                  
                  <div className="agent-meta">
                    <div className="meta-item">
                      <span className="meta-label">Rating:</span>
                      <span className="meta-value">⭐ {agent.rating}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Retention:</span>
                      <span className="meta-value">{agent.retention}</span>
                    </div>
                  </div>
                  
                  <p className="agent-activity">{agent.activity}</p>
                  
                  <div className="agent-footer">
                    <div className="agent-price">{agent.price}</div>
                    <button 
                      className="btn btn-primary"
                      onClick={() => handleStartTrial(agent.id)}
                    >
                      Start 7-Day Trial
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {filteredAgents.length === 0 && !loading && (
          <div className="no-results">
            <p>No agents found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Marketplace;
