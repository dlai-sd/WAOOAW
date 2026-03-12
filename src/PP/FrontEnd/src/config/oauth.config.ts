interface EnvironmentConfig {
  name: string
  apiBaseUrl: string
  frontendUrl: string
  googleClientId: string
}

interface ApiEndpoints {
  googleLogin: string
  googleCallback: string
  googleVerify: string
  refresh: string
  logout: string
  me: string
}

type PPRuntimeConfig = Partial<{
  environment: string
  apiBaseUrl: string
  googleClientId: string
}>

function getPPRuntimeConfig(): PPRuntimeConfig {
  const w = window as any
  return ((w && w.__WAOOAW_PP_RUNTIME_CONFIG__) || {}) as PPRuntimeConfig
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
  if (hostname.includes('localhost') || hostname === '127.0.0.1') {
    return 'development'
  }
  if (hostname.includes('waooaw.com')) {
    return 'prod'
  }

  return 'development'
}

export function getEnvironmentConfig(): EnvironmentConfig {
  const runtime = getPPRuntimeConfig()
  const env = runtime.environment || import.meta.env.VITE_ENVIRONMENT || detectEnvironment()
  const protocol = window.location.protocol
  const hostname = window.location.hostname

  if (env === 'codespace' && hostname.includes('github.dev')) {
    const currentUrl = `${protocol}//${hostname}`

    return {
      name: 'codespace',
      apiBaseUrl: runtime.apiBaseUrl || import.meta.env.VITE_API_BASE_URL || `${currentUrl}/api`,
      frontendUrl: currentUrl,
      googleClientId: runtime.googleClientId || import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    }
  }

  const configs: Record<string, EnvironmentConfig> = {
    demo: {
      name: 'demo',
      apiBaseUrl: runtime.apiBaseUrl || 'https://pp.demo.waooaw.com/api',
      frontendUrl: 'https://pp.demo.waooaw.com',
      googleClientId: runtime.googleClientId || import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    uat: {
      name: 'uat',
      apiBaseUrl: runtime.apiBaseUrl || 'https://pp.uat.waooaw.com/api',
      frontendUrl: 'https://pp.uat.waooaw.com',
      googleClientId: runtime.googleClientId || import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    prod: {
      name: 'prod',
      apiBaseUrl: runtime.apiBaseUrl || 'https://platform.waooaw.com/api',
      frontendUrl: 'https://platform.waooaw.com',
      googleClientId: runtime.googleClientId || import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    },
    development: {
      name: 'development',
      apiBaseUrl: runtime.apiBaseUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8015/api',
      frontendUrl: 'http://localhost:3000',
      googleClientId: runtime.googleClientId || import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    }
  }

  return configs[env] || configs.development
}

export function getApiEndpoints(): ApiEndpoints {
  const currentConfig = getEnvironmentConfig()

  return {
    googleLogin: `${currentConfig.apiBaseUrl}/auth/google/login`,
    googleCallback: `${currentConfig.apiBaseUrl}/auth/google/callback`,
    googleVerify: `${currentConfig.apiBaseUrl}/auth/google/verify`,
    refresh: `${currentConfig.apiBaseUrl}/auth/refresh`,
    logout: `${currentConfig.apiBaseUrl}/auth/logout`,
    me: `${currentConfig.apiBaseUrl}/auth/me`
  }
}

export const config: EnvironmentConfig = {
  get name() {
    return getEnvironmentConfig().name
  },
  get apiBaseUrl() {
    return getEnvironmentConfig().apiBaseUrl
  },
  get frontendUrl() {
    return getEnvironmentConfig().frontendUrl
  },
  get googleClientId() {
    return getEnvironmentConfig().googleClientId
  }
}

export const API_ENDPOINTS: ApiEndpoints = {
  get googleLogin() {
    return getApiEndpoints().googleLogin
  },
  get googleCallback() {
    return getApiEndpoints().googleCallback
  },
  get googleVerify() {
    return getApiEndpoints().googleVerify
  },
  get refresh() {
    return getApiEndpoints().refresh
  },
  get logout() {
    return getApiEndpoints().logout
  },
  get me() {
    return getApiEndpoints().me
  }
}

export default config
