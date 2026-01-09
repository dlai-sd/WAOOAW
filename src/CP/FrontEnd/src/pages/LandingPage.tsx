import HeroSection from '../sections/HeroSection'
import MarketplaceSection from '../sections/MarketplaceSection'
import HowItWorksSection from '../sections/HowItWorksSection'
import FeaturesSection from '../sections/FeaturesSection'
import CTASection from '../sections/CTASection'
import Footer from '../components/Footer'

export default function LandingPage() {
  return (
    <main>
      <HeroSection />
      <MarketplaceSection />
      <HowItWorksSection />
      <FeaturesSection />
      <CTASection />
      <Footer />
    </main>
  )
}
