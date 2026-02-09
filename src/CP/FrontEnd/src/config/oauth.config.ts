/**
 * OAuth and API configuration
 * Environment-specific settings for authentication
 */

interface EnvironmentConfig {
  name: string
  apiBaseUrl: string
  frontendUrl: string
  googleClientId: string
}

/**
 * Detect current environment based on hostname
 */
function detectEnvironment(): string {
  const hostname = window.location?.hostname || ''
  
  if (hostname.includes('github.dev') || hostname.includes('gitpod.io')) {
    return 'codespace'
  }
  if (hostname.includes('demo.waooaw.com')) {
    return 'demo'
  }
  if (hostname.includes('uat.waooaw.com')) {
    return 'uat'
  }
  if (hostname.includes('localhost') || hostname === '127.0.0.1') {
    return 'development'
  }
  if (hostname.includes('waooaw.com')) {
    return 'prod'
  }
  
  return 'development'
}

/**
 * Get environment-specific configuration
 */
function getEnvironmentConfig(): EnvironmentConfig {
  const env = import.meta.env.VITE_ENVIRONMENT || detectEnvironment()
  const protocol = window.location?.protocol || 'http:'
  const hostname = window.location?.hostname || ''
  
  // For Codespace, dynamically construct URLs
  if (env === 'codespace' && hostname.includes('github.dev')) {
    // We're using single port architecture - everything on 8000
    const currentUrl = `${protocol}//${hostname}`
    
    return {
      name: 'codespace',
      apiBaseUrl: `${currentUrl}/api`,
      frontendUrl: currentUrl,
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    }
  }
  
  // Environment-specific configs
  const configs: Record<string, EnvironmentConfig> = {
    demo: {
      name: 'demo',
      apiBaseUrl: 'https://cp.demo.waooaw.com/api',
      frontendUrl: 'https://cp.demo.waooaw.com',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    uat: {
      name: 'uat',
      apiBaseUrl: 'https://cp.uat.waooaw.com/api',
      frontendUrl: 'https://cp.uat.waooaw.com',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    prod: {
      name: 'prod',
      apiBaseUrl: 'https://cp.waooaw.com/api',
      frontendUrl: 'https://cp.waooaw.com',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    development: {
      name: 'development',
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
      frontendUrl: 'http://localhost:3000',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    }
  }
  
  return configs[env] || configs.development
}

// Export current configuration
export const config = getEnvironmentConfig()

export const API_ENDPOINTS = {
  // Auth endpoints
  googleLogin: `${config.apiBaseUrl}/auth/google/login`,
  googleCallback: `${config.apiBaseUrl}/auth/google/callback`,
  googleVerify: `${config.apiBaseUrl}/auth/google/verify`,
  logout: `${config.apiBaseUrl}/auth/logout`,
  me: `${config.apiBaseUrl}/auth/me`,
  
  // Future endpoints
  agents: `${config.apiBaseUrl}/agents`,
  trials: `${config.apiBaseUrl}/trials`,
  subscriptions: `${config.apiBaseUrl}/subscriptions`
}

export default config
