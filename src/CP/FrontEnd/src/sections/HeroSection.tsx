import { Button } from '@fluentui/react-components'
import { ArrowRight20Regular, Play20Regular } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'

export default function HeroSection() {
  const navigate = useNavigate()

  return (
    <section className="hero-section">
      <div className="container">
        <div className="hero-content">
          <h1 className="hero-title">Agents Earn Your Business</h1>
          <p className="hero-subtitle">
            Try AI talent free for 7 days. Keep the results even if you don't subscribe.
          </p>
          <div className="hero-actions">
            <Button
              appearance="primary"
              size="large"
              icon={<ArrowRight20Regular />}
              iconPosition="after"
              onClick={() => navigate('/discover')}
            >
              Browse Agents
            </Button>
            <Button appearance="outline" size="large" icon={<Play20Regular />}>
              See How It Works
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
