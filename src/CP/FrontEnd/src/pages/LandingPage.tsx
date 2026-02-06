import { useState } from 'react'
import { Card, Text } from '@fluentui/react-components'
import HeroSection from '../sections/HeroSection'
import MarketplaceSection from '../sections/MarketplaceSection'
import HowItWorksSection from '../sections/HowItWorksSection'
import FeaturesSection from '../sections/FeaturesSection'
import CTASection from '../sections/CTASection'
import Footer from '../components/Footer'
import { consumeAuthExpiredFlag } from '../context/AuthContext'

export default function LandingPage() {
  const [sessionExpired] = useState(() => consumeAuthExpiredFlag())

  return (
    <main>
      {sessionExpired && (
        <div style={{ padding: '1rem' }}>
          <Card>
            <div style={{ padding: '1rem' }}>
              <Text weight="semibold">Session expired</Text>
              <div style={{ marginTop: '0.25rem' }}>
                <Text>Your session has expired. Please sign in again.</Text>
              </div>
            </div>
          </Card>
        </div>
      )}
      <HeroSection />
      <MarketplaceSection />
      <HowItWorksSection />
      <FeaturesSection />
      <CTASection />
      <Footer />
    </main>
  )
}
