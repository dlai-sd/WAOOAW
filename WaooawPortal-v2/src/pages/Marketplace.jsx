import { useState, useEffect } from 'react';
import config from '../config';
import '../styles/Marketplace.css';

function Marketplace() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    industry: 'all',
    search: ''
  });

  useEffect(() => {
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
    const token = localStorage.getItem('waooaw_token');
    if (!token) {
      window.location.href = `${config.apiUrl}/auth/login?frontend=www`;
    } else {
      // Start trial logic
      console.log('Starting trial for agent:', agentId);
    }
  };

  return (
    <div className="marketplace">
      <div className="container">
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
