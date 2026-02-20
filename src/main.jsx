import '@mcp-b/global'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Suppress console spam when server is down and WebMCP native-adapter noise
const suppressNoise = (originalFn) => {
  return (...args) => {
    const message = args.join(' ')
    if (
      message.includes('ERR_CONNECTION_REFUSED') ||
      message.includes('server connection lost') ||
      message.includes('Polling for restart') ||
      message.includes('net::ERR_CONNECTION_REFUSED') ||
      message.includes('Failed to fetch') ||
      (message.includes('GET') && message.includes('localhost:5173') && message.includes('ERR_CONNECTION_REFUSED')) ||
      message.includes('listTools is not a function') ||
      message.includes('[WebModelContext]') ||
      message.includes('Auto-initialization failed') ||
      message.includes('Failed to initialize native adapter')
    ) {
      return
    }
    originalFn.apply(console, args)
  }
}

console.error = suppressNoise(console.error)
console.warn = suppressNoise(console.warn)

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

