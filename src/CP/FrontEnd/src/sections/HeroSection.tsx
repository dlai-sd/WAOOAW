import { Button } from '@fluentui/react-components'
import { ArrowRight20Regular, Play20Regular } from '@fluentui/react-icons'
import { useNavigate } from 'react-router-dom'

function HeroIllustration() {
  return (
    <svg
      viewBox="0 0 560 420"
      role="img"
      aria-label="Abstract AI automation illustration"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <linearGradient id="waooawGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="var(--colorBrandForeground1)" stopOpacity="1" />
          <stop offset="1" stopColor="var(--colorBrandBackground)" stopOpacity="1" />
        </linearGradient>
      </defs>

      <rect x="24" y="28" width="512" height="320" rx="24" fill="var(--colorNeutralBackground1)" stroke="var(--colorNeutralStroke2)" />
      <rect x="52" y="64" width="260" height="22" rx="8" fill="var(--colorNeutralBackground3)" />
      <rect x="52" y="98" width="340" height="14" rx="7" fill="var(--colorNeutralBackground3)" />
      <rect x="52" y="120" width="300" height="14" rx="7" fill="var(--colorNeutralBackground3)" />

      <rect x="52" y="168" width="456" height="156" rx="18" fill="var(--colorNeutralBackground3)" />

      <circle cx="414" cy="128" r="54" fill="url(#waooawGradient)" opacity="0.22" />
      <circle cx="454" cy="104" r="18" fill="url(#waooawGradient)" opacity="0.38" />
      <circle cx="370" cy="102" r="12" fill="url(#waooawGradient)" opacity="0.28" />

      <path
        d="M126 248c40-48 96-72 152-50 34 14 50 44 92 44 48 0 74-38 104-70"
        fill="none"
        stroke="url(#waooawGradient)"
        strokeWidth="10"
        strokeLinecap="round"
        opacity="0.6"
      />
      <path
        d="M108 268c46-36 92-46 132-22 22 14 44 36 86 34 44-2 74-34 128-88"
        fill="none"
        stroke="var(--colorBrandForeground1)"
        strokeWidth="6"
        strokeLinecap="round"
        opacity="0.45"
      />

      <rect x="64" y="362" width="176" height="30" rx="12" fill="url(#waooawGradient)" opacity="0.25" />
      <rect x="252" y="362" width="132" height="30" rx="12" fill="var(--colorNeutralBackground3)" />
      <rect x="394" y="362" width="128" height="30" rx="12" fill="var(--colorNeutralBackground3)" />
    </svg>
  )
}

export default function HeroSection() {
  const navigate = useNavigate()

  return (
    <section className="hero-section">
      <div className="container">
        <div className="hero-layout">
          <div className="hero-content">
            <h1 className="hero-title">Hire AI Talent That Earns Your Trust and Business</h1>
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
