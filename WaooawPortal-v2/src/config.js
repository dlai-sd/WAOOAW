// Environment detection for WaooawPortal
function detectEnvironment() {
  const hostname = window.location.hostname;
  
  if (hostname.includes('demo-www') || hostname.includes('demo.waooaw')) {
    return 'demo';
  } else if (hostname.includes('uat-www') || hostname.includes('uat.waooaw')) {
    return 'uat';
  } else if (hostname === 'www.waooaw.com') {
    return 'production';
  }
  // Development
  return 'development';
}

const ENV = detectEnvironment();

// API URLs per environment
const API_URLS = {
  development: 'http://localhost:8000',
  demo: 'https://demo-api.waooaw.com',
  uat: 'https://uat-api.waooaw.com',
  production: 'https://api.waooaw.com'
};

export const config = {
  env: ENV,
  apiUrl: API_URLS[ENV],
  isDevelopment: ENV === 'development',
  isDemo: ENV === 'demo',
  isUAT: ENV === 'uat',
  isProduction: ENV === 'production'
};

export default config;
