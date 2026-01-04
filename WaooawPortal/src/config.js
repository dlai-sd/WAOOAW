// Environment detection for WaooawPortal
function detectEnvironment() {
  const hostname = window.location.hostname;
  
  // Codespace detection (runs first)
  if (hostname.includes('app.github.dev')) {
    return 'codespace';
  }
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

// Auto-detect Codespace backend URL from portal's own URL
function getCodespaceBackendUrl() {
  const hostname = window.location.hostname;
  // Format: shiny-space-guide-pj4gwgp94gw93557-8080.app.github.dev
  // Extract codespace name and replace port with 8000
  const match = hostname.match(/^(.+)-\d+\.app\.github\.dev$/);
  if (match) {
    const codespaceName = match[1];
    return `https://${codespaceName}-8000.app.github.dev`;
  }
  return 'http://localhost:8000'; // fallback
}

const ENV = detectEnvironment();

// API URLs per environment
const API_URLS = {
  development: 'http://localhost:8000',
  codespace: getCodespaceBackendUrl(),
  demo: 'https://waooaw-api-demo-ryvhxvrdna-el.a.run.app',  // Cloud Run URL (asia-south1 limitation)
  uat: 'https://uat-api.waooaw.com',  // Will use Load Balancer
  production: 'https://api.waooaw.com'  // Will use Load Balancer
};

export const config = {
  env: ENV,
  apiUrl: API_URLS[ENV],
  isDevelopment: ENV === 'development',
  isCodespace: ENV === 'codespace',
  isDemo: ENV === 'demo',
  isUAT: ENV === 'uat',
  isProduction: ENV === 'production'
};

export default config;
