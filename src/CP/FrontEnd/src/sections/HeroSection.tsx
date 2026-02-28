import { Button } from '@fluentui/react-components'
import { ArrowRight20Regular, Play20Regular } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'

import HeroCarousel, { SLIDE_COUNT } from '../components/HeroCarousel'

const ROTATING_WORDS = ['Talent', 'Agents', 'Workforce', 'Partners']
const INTERVAL_MS = 4000

export default function HeroSection() {
  const navigate = useNavigate()
  const [slideIndex, setSlideIndex] = useState(0)
  const [wordIndex, setWordIndex] = useState(0)
  const slideRef = useRef(slideIndex)
  const wordRef = useRef(wordIndex)
  slideRef.current = slideIndex
  wordRef.current = wordIndex

  // Word-only auto-rotation — image is user-controlled via arrows
  useEffect(() => {
    const t = setInterval(() => {
      setWordIndex((wordRef.current + 1) % ROTATING_WORDS.length)
    }, INTERVAL_MS)
    return () => clearInterval(t)
  }, [])

  const goPrev = () => {
    setSlideIndex((slideRef.current - 1 + SLIDE_COUNT) % SLIDE_COUNT)
  }

  const goNext = () => {
    setSlideIndex((slideRef.current + 1) % SLIDE_COUNT)
  }

  return (
    <section className="hero-section" id="home">
      <div className="container">
        <div className="hero-layout">
          <div className="hero-content">
            <h1 className="hero-title">
              <span className="hero-title-line hero-title-line--big">
                Hire AI{' '}
                <span className="hero-rotating-word">
                  {ROTATING_WORDS[wordIndex]}
                </span>
              </span>
              <span className="hero-title-line hero-title-line--second">To earn trust and business</span>
            </h1>
            <p className="hero-subtitle">
              Accelerate your business with advanced AI agents—free for 7 days, no commitment required.
              Our agents automate workflows, generate insights, and boost productivity at scale.
              Keep all your results, even if you choose not to subscribe.
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
            <HeroCarousel current={slideIndex} onPrev={goPrev} onNext={goNext} />
          </div>
        </div>
      </div>
    </section>
  )
}
