import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Suppress console spam when server is down
const suppressConnectionErrors = (originalFn) => {
  return (...args) => {
    const message = args.join(' ')
    // Suppress Vite HMR and fetch connection errors
    if (
      message.includes('ERR_CONNECTION_REFUSED') ||
      message.includes('server connection lost') ||
      message.includes('Polling for restart') ||
      message.includes('net::ERR_CONNECTION_REFUSED') ||
      message.includes('Failed to fetch') ||
      (message.includes('GET') && message.includes('localhost:5173') && message.includes('ERR_CONNECTION_REFUSED'))
    ) {
      return // Silent fail
    }
    originalFn.apply(console, args)
  }
}

// Override console.error and console.warn to suppress connection errors
console.error = suppressConnectionErrors(console.error)
console.warn = suppressConnectionErrors(console.warn)

// Register Service Worker for offline caching
// Register Service Worker for offline caching (Disabled to prevent stale cache issues)
/*
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('Service Worker registered:', registration.scope)
      })
      .catch((error) => {
        console.log('Service Worker registration failed:', error)
      })
  })
}
*/

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

