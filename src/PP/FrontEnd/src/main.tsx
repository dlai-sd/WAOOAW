import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

function loadRuntimeConfig(): Promise<void> {
  if (import.meta.env.DEV) {
    return Promise.resolve()
  }

  return new Promise((resolve) => {
    const script = document.createElement('script')
    script.src = '/pp-runtime-config.js'
    script.async = false
    script.onload = () => resolve()
    script.onerror = () => resolve()
    document.head.appendChild(script)
  })
}

void loadRuntimeConfig().finally(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
})
