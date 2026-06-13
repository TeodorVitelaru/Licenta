import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getAnimationDelay } from '../utils/animationSync'
import './Login.css'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const fieldRef = useRef(null)

  // Sincronizeaza animatia background-ului
  useEffect(() => {
    if (fieldRef.current) {
      const delay = getAnimationDelay()
      fieldRef.current.style.animationDelay = `${delay}s`
    }
  }, [])

  // Mesaj dupa inregistrare reusita
  useEffect(() => {
    if (location.state?.registrationSuccess) {
      setSuccessMessage('Contul a fost creat cu succes! Te poti conecta acum.')
      // Completeaza email-ul daca vine din pagina de register
      if (location.state?.email) {
        setEmail(location.state.email)
      }
      // Curata state-ul dupa afisarea mesajului
      window.history.replaceState({}, document.title)
    }
  }, [location])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    const result = await login(email, password)
    if (result.success) {
      navigate('/home')
    } else {
      setError(result.error)
    }
    setIsSubmitting(false)
  }

  const handleGoogleLogin = () => {
    alert('Conectare cu Google - functionalitate va fi implementata ulterior')
  }

  const handleSignUp = () => {
    navigate('/register')
  }

  const handleForgotPassword = () => {
    alert('Recuperare parola - functionalitate va fi implementata ulterior')
  }

  return (
    <div className="login-container">
      <div className="login-background">
        <div className="football-field" ref={fieldRef}>
          <svg viewBox="0 0 800 600" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Teren de fotbal */}
            <rect x="50" y="50" width="700" height="500" fill="url(#fieldGradient)" rx="20"/>
            <line x1="400" y1="50" x2="400" y2="550" stroke="white" strokeWidth="4" strokeLinecap="round"/>
            <circle cx="400" cy="300" r="80" fill="none" stroke="white" strokeWidth="3"/>
            <circle cx="400" cy="300" r="6" fill="white"/>
            
            {/* Zone de penalty */}
            <rect x="50" y="200" width="120" height="200" fill="none" stroke="white" strokeWidth="3"/>
            <rect x="50" y="250" width="60" height="100" fill="none" stroke="white" strokeWidth="3"/>
            <rect x="630" y="200" width="120" height="200" fill="none" stroke="white" strokeWidth="3"/>
            <rect x="690" y="250" width="60" height="100" fill="none" stroke="white" strokeWidth="3"/>
            
            {/* Jucatori stilizati */}
            <g transform="translate(250, 280)">
              <circle cx="0" cy="0" r="30" fill="url(#player1Gradient)"/>
              <ellipse cx="0" cy="40" rx="22" ry="28" fill="url(#player1Gradient)"/>
            </g>
            <g transform="translate(550, 320)">
              <circle cx="0" cy="0" r="30" fill="url(#player2Gradient)"/>
              <ellipse cx="0" cy="40" rx="22" ry="28" fill="url(#player2Gradient)"/>
            </g>
            
            {/* Minge */}
            <g transform="translate(450, 280)">
              <circle cx="0" cy="0" r="20" fill="url(#ballGradient)"/>
              <path d="M-16 -8 Q0 -12 16 -8 Q16 8 0 12 Q-16 8 -16 -8" stroke="white" strokeWidth="2" fill="none"/>
            </g>
            
            <defs>
              <linearGradient id="fieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.3"/>
                <stop offset="50%" stopColor="#16a34a" stopOpacity="0.25"/>
                <stop offset="100%" stopColor="#15803d" stopOpacity="0.3"/>
              </linearGradient>
              <linearGradient id="player1Gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4"/>
                <stop offset="100%" stopColor="#2563eb" stopOpacity="0.4"/>
              </linearGradient>
              <linearGradient id="player2Gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4"/>
                <stop offset="100%" stopColor="#dc2626" stopOpacity="0.4"/>
              </linearGradient>
              <linearGradient id="ballGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.6"/>
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.6"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div className="login-background-overlay"></div>
      </div>
      
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <i className="fas fa-futbol"></i>
            <span className="login-logo-text">WP</span>
          </div>
          <h1>WinProb</h1>
          <p className="login-subtitle">Autentifica-te pentru a continua</p>
        </div>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">
              <i className="fas fa-envelope"></i>
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Introdu adresa de email"
            />
          </div>
          
          <div className="form-group">
            <div className="password-label-wrapper">
              <label htmlFor="password">
                <i className="fas fa-lock"></i>
                Parola
              </label>
              <button
                type="button"
                className="forgot-password-link"
                onClick={handleForgotPassword}
              >
                Ai uitat parola?
              </button>
            </div>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Introdu parola"
            />
          </div>
          
          {error && (
            <div className="error-message">
              <i className="fas fa-exclamation-circle"></i>
              {error}
            </div>
          )}

          {successMessage && (
            <div className="success-message">
              <i className="fas fa-check-circle"></i>
              {successMessage}
            </div>
          )}
          
          <button type="submit" className="login-button" disabled={isSubmitting}>
            <i className="fas fa-sign-in-alt"></i>
            {isSubmitting ? 'Se conecteaza...' : 'Conecteaza-te'}
          </button>
        </form>
        
        <div className="login-divider">
          <span>sau</span>
        </div>
        
        <button 
          type="button" 
          className="google-login-button"
          onClick={handleGoogleLogin}
        >
          <i className="fab fa-google"></i>
          <span>Conecteaza-te cu Google</span>
        </button>
        
        <div className="signup-section">
          <p className="signup-text">
            Nu ai cont?{' '}
            <button 
              type="button" 
              className="signup-link"
              onClick={handleSignUp}
            >
              Inregistreaza-te
            </button>
          </p>
        </div>
        
        <div className="login-hint">
          <div className="hint-header">
            <i className="fas fa-server"></i>
            <span>Adresa API</span>
          </div>
          <div className="hint-credentials">
            <div className="credential-item">
              <span className="credential-label">API:</span>
              <span className="credential-value">http://localhost:8000</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
