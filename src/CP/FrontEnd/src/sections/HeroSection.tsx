import { Button } from '@fluentui/react-components'
import { ArrowRight20Regular, Play20Regular } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'

import heroBanner from '../WaooaW banner.png'

const ROTATING_WORDS = ['Talent', 'Agents', 'Workforce', 'Partners']

function HeroIllustration() {
  return (
    <img src={heroBanner} alt="WAOOAW hero banner" />
  )
}

export default function HeroSection() {
  const navigate = useNavigate()
  const [wordIndex, setWordIndex] = useState(0)
  const [animating, setAnimating] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setAnimating(true)
      setTimeout(() => {
        setWordIndex((i) => (i + 1) % ROTATING_WORDS.length)
        setAnimating(false)
      }, 300)
    }, 2800)
    return () => clearInterval(interval)
  }, [])

  return (
    <section className="hero-section" id="home">
      <div className="container">
        <div className="hero-layout">
          <div className="hero-content">
            <h1 className="hero-title">
              <span className="hero-title-line hero-title-line--big">
                Hire AI{' '}
                <span
                  className={`hero-rotating-word${animating ? ' hero-rotating-word--out' : ''}`}
                >
                  {ROTATING_WORDS[wordIndex]}
                </span>
              </span>
              <span className="hero-title-line">To earn trust and business</span>
            </h1>
            <p className="hero-subtitle">
              Accelerate your business operations with our advanced AI agents. Try our premium AI talent free for 7 days—no
              commitment required. See firsthand how our agents can automate workflows, generate insights, and boost
              productivity. Keep all your results, even if you choose not to subscribe.
            </p>
            <div className="hero-actions">
              <Button
                className="hero-cta hero-cta--primary"
                appearance="primary"
                size="large"
                icon={<ArrowRight20Regular />}
                iconPosition="after"
                onClick={() => navigate('/discover')}
              >
                Browse Agents
              </Button>
              <Button className="hero-cta hero-cta--secondary" appearance="outline" size="large" icon={<Play20Regular />}>
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
