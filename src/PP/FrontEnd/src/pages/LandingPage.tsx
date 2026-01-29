import { Card, Text } from '@fluentui/react-components'
import { Bot24Regular, ShieldTask24Regular, Certificate24Regular } from '@fluentui/react-icons'

export default function LandingPage() {
  return (
    <div className="landing-page">
      <div className="landing-hero">
        <div className="hero-content">
          <Text as="h1" size={1000} weight="bold" className="hero-title">
            WAOOAW Platform Portal
          </Text>
        </div>
      </div>

      <div className="landing-features">
        <Card className="feature-card">
          <Bot24Regular fontSize={48} style={{ color: '#4da6ff', marginBottom: '16px' }} />
          <Text size={600} weight="semibold">Agent Management</Text>
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
