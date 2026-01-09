import { Button } from '@fluentui/react-components'
import { Sparkle20Regular, Chat20Regular } from '@fluentui/react-icons'

export default function CTASection() {
  return (
    <section className="cta-section">
      <div className="container">
        <h2>Ready to transform your team?</h2>
        <p>Start your free trial today. No credit card required.</p>
        <div className="cta-actions">
          <Button appearance="primary" size="large" icon={<Sparkle20Regular />}>
            Start Free Trial
          </Button>
          <Button appearance="outline" size="large" icon={<Chat20Regular />}>
            Talk to Sales
          </Button>
        </div>
      </div>
    </section>
  )
}
