import { useState } from 'react'
import { FluentProvider } from '@fluentui/react-components'
import { waooawLightTheme, waooawDarkTheme } from './theme'
import Header from './components/Header'
import HeroSection from './sections/HeroSection'
import MarketplaceSection from './sections/MarketplaceSection'
import HowItWorksSection from './sections/HowItWorksSection'
import FeaturesSection from './sections/FeaturesSection'
import CTASection from './sections/CTASection'
import Footer from './components/Footer'

function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <FluentProvider theme={theme === 'light' ? waooawLightTheme : waooawDarkTheme}>
      <div className="app">
        <Header theme={theme} toggleTheme={toggleTheme} />
        <main>
          <HeroSection />
          <MarketplaceSection />
          <HowItWorksSection />
          <FeaturesSection />
          <CTASection />
        </main>
        <Footer />
      </div>
    </FluentProvider>
  )
}

export default App
