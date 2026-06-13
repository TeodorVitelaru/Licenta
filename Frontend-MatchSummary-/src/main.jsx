import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { authService } from './services'
import './index.css'

// Initializeaza autentificarea la start
authService.initAuth()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

