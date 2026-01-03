// Environment detection for WaooawPortal
function detectEnvironment() {
  const hostname = window.location.hostname;
  
  // Cloud Run demo environment
  if (hostname.includes('waooaw-portal-demo') || hostname.includes('demo-www') || hostname.includes('demo.waooaw')) {
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
  demo: 'https://waooaw-api-demo-ryvhxvrdna-el.a.run.app',  // Cloud Run URL (asia-south1 limitation)
  uat: 'https://uat-api.waooaw.com',  // Will use Load Balancer
  production: 'https://api.waooaw.com'  // Will use Load Balancer
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
