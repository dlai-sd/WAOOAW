import React from 'react'
import ReactDOM from 'react-dom/client'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App'
import './styles/globals.css'
import config from './config/oauth.config'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {config.googleClientId ? (
      <GoogleOAuthProvider clientId={config.googleClientId}>
        <App />
      </GoogleOAuthProvider>
    ) : (
      <App />
    )}
  </React.StrictMode>,
)
