import { Card, Text } from '@fluentui/react-components'
import { Bot24Regular, ShieldTask24Regular, Certificate24Regular } from '@fluentui/react-icons'

export default function LandingPage() {
  return (
    <div className="landing-page" data-testid="pp-landing-page">
      <div className="landing-hero">
        <div className="hero-content">
          <Text as="h1" size={1000} weight="bold" className="hero-title">
            WAOOAW Platform Portal
          </Text>
          <Text size={500} className="hero-subtitle">
            The control plane for contributors who shape, govern, and defend the WAOOAW marketplace.
          </Text>
          <div className="pp-landing-proof-row">
            <span className="pp-landing-proof-pill">Ops-ready</span>
            <span className="pp-landing-proof-pill">Policy-aware</span>
            <span className="pp-landing-proof-pill">Agentic by design</span>
          </div>
        </div>
      </div>

      <div className="pp-landing-role-grid">
        <Card className="feature-card">
          <Text size={600} weight="semibold">Tech + product</Text>
          <Text size={300}>Author and publish agent definitions with stronger readiness and simulation expectations.</Text>
        </Card>
        <Card className="feature-card">
          <Text size={600} weight="semibold">Ops + helpdesk</Text>
          <Text size={300}>See incidents, approvals, and customer-impacting issues earlier.</Text>
        </Card>
        <Card className="feature-card">
          <Text size={600} weight="semibold">Infra + governance</Text>
          <Text size={300}>Keep the runtime healthy while preserving auditability and release discipline.</Text>
        </Card>
      </div>

      <div className="landing-features">
        <Card className="feature-card">
          <Bot24Regular fontSize={48} style={{ color: '#4da6ff', marginBottom: '16px' }} />
          <Text size={600} weight="semibold">Agent Management</Text>
          <Text size={300} style={{ marginTop: '8px', opacity: 0.8 }}>
            Manage hireable supply with stronger structure across agents, skills, and components.
          </Text>
        </Card>

        <Card className="feature-card">
          <ShieldTask24Regular fontSize={48} style={{ color: '#4da6ff', marginBottom: '16px' }} />
          <Text size={600} weight="semibold">Governor Console</Text>
          <Text size={300} style={{ marginTop: '8px', opacity: 0.8 }}>
            Approve deployments, manage policies, oversee operations
          </Text>
        </Card>

        <Card className="feature-card">
          <Certificate24Regular fontSize={48} style={{ color: '#4da6ff', marginBottom: '16px' }} />
          <Text size={600} weight="semibold">Genesis Console</Text>
          <Text size={300} style={{ marginTop: '8px', opacity: 0.8 }}>
            Certify agent skills, manage capabilities library
          </Text>
        </Card>
      </div>
    </div>
  )
}
