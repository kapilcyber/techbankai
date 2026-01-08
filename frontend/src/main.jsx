import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

// Check if root element exists
const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found! Check index.html for <div id="root"></div>')
}

console.log('🚀 Starting React app...')
console.log('Root element:', rootElement)

try {
  const root = ReactDOM.createRoot(rootElement)
  console.log('✅ React root created')

  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <GoogleOAuthProvider clientId="646588737744-ervf3j64kdic8iektcc9sflflm3c7iie.apps.googleusercontent.com">
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </GoogleOAuthProvider>
      </ErrorBoundary>
    </React.StrictMode>,
  )
  console.log('✅ React app rendered')
} catch (error) {
  console.error('❌ Failed to render React app:', error)
  rootElement.innerHTML = `
    <div style="padding: 20px; color: red; font-family: Arial; background: white; min-height: 100vh;">
      <h1>Failed to load application</h1>
      <p><strong>Error:</strong> ${error.message}</p>
      <p><strong>Stack:</strong></p>
      <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">${error.stack}</pre>
      <p>Check the browser console (F12) for more details.</p>
    </div>
  `
}

