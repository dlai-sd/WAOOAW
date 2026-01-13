interface EnvironmentConfig {
  name: string
  apiBaseUrl: string
  frontendUrl: string
  googleClientId: string
}

function detectEnvironment(): string {
  const hostname = window.location.hostname

  if (hostname.includes('github.dev') || hostname.includes('gitpod.io')) {
    return 'codespace'
  }
  if (hostname.includes('demo.waooaw.com')) {
    return 'demo'
  }
  if (hostname.includes('uat.waooaw.com')) {
    return 'uat'
  }
  if (hostname.includes('waooaw.com') || hostname.includes('localhost')) {
    return 'prod'
  }

  return 'development'
}

function getEnvironmentConfig(): EnvironmentConfig {
  const env = import.meta.env.VITE_ENVIRONMENT || detectEnvironment()
  const protocol = window.location.protocol
  const hostname = window.location.hostname

  if (env === 'codespace' && hostname.includes('github.dev')) {
    const currentUrl = `${protocol}//${hostname}`

    return {
      name: 'codespace',
      apiBaseUrl: `${currentUrl}/api`,
      frontendUrl: currentUrl,
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    }
  }

  const configs: Record<string, EnvironmentConfig> = {
    demo: {
      name: 'demo',
      apiBaseUrl: 'https://pp.demo.waooaw.com/api',
      frontendUrl: 'https://pp.demo.waooaw.com',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    uat: {
      name: 'uat',
      apiBaseUrl: 'https://pp.uat.waooaw.com/api',
      frontendUrl: 'https://pp.uat.waooaw.com',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    prod: {
      name: 'prod',
      apiBaseUrl: 'https://platform.waooaw.com/api',
      frontendUrl: 'https://platform.waooaw.com',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    development: {
      name: 'development',
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8015/api',
      frontendUrl: 'http://localhost:3000',
      googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    }
  }

  return configs[env] || configs.development
}

export const config = getEnvironmentConfig()

export const API_ENDPOINTS = {
  googleLogin: `${config.apiBaseUrl}/auth/google/login`,
  googleCallback: `${config.apiBaseUrl}/auth/google/callback`,
  googleVerify: `${config.apiBaseUrl}/auth/google/verify`,
  refresh: `${config.apiBaseUrl}/auth/refresh`,
  logout: `${config.apiBaseUrl}/auth/logout`,
  me: `${config.apiBaseUrl}/auth/me`
}

export default config
