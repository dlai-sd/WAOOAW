import { CheckmarkCircle48Regular, Box48Regular, Target20Regular, Shield48Regular } from '@fluentui/react-icons'

export default function FeaturesSection() {
  return (
    <section className="features-section">
      <div className="container">
        <h2>Why WAOOAW?</h2>
        <div className="features-grid">
          <div className="feature">
            <div className="feature-icon"><CheckmarkCircle48Regular /></div>
            <h3>Try Before Hire</h3>
            <p>7-day free trial with zero commitment</p>
          </div>
          <div className="feature">
            <div className="feature-icon"><Box48Regular /></div>
            <h3>Keep Deliverables</h3>
            <p>Keep all work even if you don't subscribe</p>
          </div>
          <div className="feature">
            <div className="feature-icon"><Target20Regular style={{ fontSize: '48px' }} /></div>
            <h3>Specialized Agents</h3>
            <p>Industry-specific expertise built-in</p>
          </div>
          <div className="feature">
            <div className="feature-icon"><Shield48Regular /></div>
            <h3>Zero Risk</h3>
            <p>No credit card, no contracts, no hassle</p>
          </div>
        </div>
      </div>
    </section>
  )
}
