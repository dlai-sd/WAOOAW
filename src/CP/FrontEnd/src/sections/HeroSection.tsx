import { Button } from '@fluentui/react-components'
import { ArrowRight20Regular, Play20Regular } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'

import heroBanner from '../WaooaW banner.png'

function HeroIllustration() {
  return (
    <img
      src={heroBanner}
      alt="WAOOAW hero banner"
      style={{ width: '100%', height: 'auto', display: 'block' }}
    />
  )
}

export default function HeroSection() {
  const navigate = useNavigate()

  return (
    <section className="hero-section">
      <div className="container">
        <div className="hero-layout">
          <div className="hero-content">
            <h1 className="hero-title">
              <span className="hero-title-line hero-title-line--big">Hire AI Talent</span>
              <span className="hero-title-line">That earns your trust and business</span>
            </h1>
            <p className="hero-subtitle">
              Accelerate your business operations with our advanced AI agents. Try our premium AI talent free for 7 days—no
              commitment required. See firsthand how our agents can automate workflows, generate insights, and boost
              productivity. Keep all your results, even if you choose not to subscribe.
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

          <div className="hero-media" aria-hidden="true">
            <HeroIllustration />
          </div>
        </div>
      </div>
    </section>
  )
}
