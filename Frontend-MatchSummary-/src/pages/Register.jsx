import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getAnimationDelay } from '../utils/animationSync'
import './Register.css'

const Register = () => {
  const navigate = useNavigate()
  const { register } = useAuth()

  // State formular
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    password: '',
    confirmPassword: '',
  })

  // State UI
  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const fieldRef = useRef(null)

  // Sincronizeaza animatia background-ului
  useEffect(() => {
    if (fieldRef.current) {
      const delay = getAnimationDelay()
      fieldRef.current.style.animationDelay = `${delay}s`
    }
  }, [])

  // Validare campuri
  const validateField = (name, value) => {
    const newErrors = { ...errors }
    
    switch (name) {
      case 'email':
        if (!value.trim()) {
          newErrors.email = 'Email-ul este obligatoriu'
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          newErrors.email = 'Email-ul nu este valid'
        } else {
          delete newErrors.email
        }
        break

      case 'name':
        if (!value.trim()) {
          newErrors.name = 'Numele este obligatoriu'
        } else if (value.length < 2) {
          newErrors.name = 'Numele trebuie sa aiba minim 2 caractere'
        } else {
          delete newErrors.name
        }
        break

      case 'password':
        if (!value) {
          newErrors.password = 'Parola este obligatorie'
        } else if (value.length < 8) {
          newErrors.password = 'Parola trebuie sa aiba minim 8 caractere'
        } else if (!/(?=.*[a-z])(?=.*[A-Z])/.test(value)) {
          newErrors.password = 'Parola trebuie sa contina cel putin o litera mica si una mare'
        } else {
          delete newErrors.password
          // Re-valideaza confirmarea parolei daca exista
          if (formData.confirmPassword) {
            if (value !== formData.confirmPassword) {
              newErrors.confirmPassword = 'Parolele nu se potrivesc'
            } else {
              delete newErrors.confirmPassword
            }
          }
        }
        break

      case 'confirmPassword':
        if (!value) {
          newErrors.confirmPassword = 'Te rog confirma parola'
        } else if (value !== formData.password) {
          newErrors.confirmPassword = 'Parolele nu se potrivesc'
        } else {
          delete newErrors.confirmPassword
        }
        break

      default:
        break
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // La schimbarea unui camp
  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))

    // Sterge mesajul de succes cand user-ul scrie
    if (successMessage) {
      setSuccessMessage('')
    }

    // Valideaza campul dupa ce user-ul a interactionat cu el
    if (errors[name]) {
      validateField(name, value)
    }
  }

  // Valideaza campul cand user-ul paraseste input-ul
  const handleBlur = (e) => {
    const { name, value } = e.target
    validateField(name, value)
  }

  // Trimite formularul
  const handleSubmit = async (e) => {
    e.preventDefault()
    setSuccessMessage('')
    
    // Valideaza toate campurile
    const fieldsToValidate = ['email', 'name', 'password', 'confirmPassword']
    let isValid = true
    
    fieldsToValidate.forEach(field => {
      if (!validateField(field, formData[field])) {
        isValid = false
      }
    })

    if (!isValid) {
      return
    }

    setIsSubmitting(true)
    setErrors({})

    try {
      const result = await register({
        email: formData.email,
        full_name: formData.name,
        name: formData.name,
        password: formData.password,
      })

      if (result.success) {
        setSuccessMessage(result.message || 'Contul a fost creat cu succes!')
        
        // Redirect la login dupa 2 secunde
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              registrationSuccess: true,
              email: formData.email 
            } 
          })
        }, 2000)
      } else {
        setErrors({ submit: result.error || 'Eroare la crearea contului' })
      }
    } catch (error) {
      setErrors({ submit: error.message || 'A aparut o eroare. Te rog incearca din nou.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="register-container">
      <div className="register-background">
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
        <div className="register-background-overlay"></div>
      </div>

      <div className="register-card">
        <div className="register-header">
          <div className="register-logo">
            <i className="fas fa-futbol"></i>
            <span className="register-logo-text">WP</span>
          </div>
          <h1>Creare Cont</h1>
          <p className="register-subtitle">Completeaza formularul pentru a-ti crea contul</p>
        </div>

        <form onSubmit={handleSubmit} className="register-form" noValidate>
          {/* Email */}
          <div className="form-group">
            <label htmlFor="email">
              <i className="fas fa-envelope"></i>
              Email <span className="required">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              onBlur={handleBlur}
              required
              placeholder="Introdu email-ul"
              className={errors.email ? 'input-error' : ''}
              autoComplete="email"
            />
            {errors.email && (
              <div className="field-error">
                <i className="fas fa-exclamation-circle"></i>
                {errors.email}
              </div>
            )}
          </div>

          {/* Name */}
          <div className="form-group">
            <label htmlFor="name">
              <i className="fas fa-id-card"></i>
              Nume complet <span className="required">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              onBlur={handleBlur}
              required
              placeholder="Introdu numele complet"
              className={errors.name ? 'input-error' : ''}
              autoComplete="name"
            />
            {errors.name && (
              <div className="field-error">
                <i className="fas fa-exclamation-circle"></i>
                {errors.name}
              </div>
            )}
          </div>

          {/* Password */}
          <div className="form-group">
            <label htmlFor="password">
              <i className="fas fa-lock"></i>
              Parola <span className="required">*</span>
            </label>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                onBlur={handleBlur}
                required
                placeholder="Introdu parola"
                className={errors.password ? 'input-error' : ''}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Ascunde parola' : 'Arata parola'}
              >
                <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
              </button>
            </div>
            {errors.password && (
              <div className="field-error">
                <i className="fas fa-exclamation-circle"></i>
                {errors.password}
              </div>
            )}
            <div className="password-hint">
              <i className="fas fa-info-circle"></i>
              <span>Minim 8 caractere, cel putin o litera mica si una mare</span>
            </div>
          </div>

          {/* Confirm Password */}
          <div className="form-group">
            <label htmlFor="confirmPassword">
              <i className="fas fa-lock"></i>
              Confirma parola <span className="required">*</span>
            </label>
            <div className="password-input-wrapper">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                onBlur={handleBlur}
                required
                placeholder="Confirma parola"
                className={errors.confirmPassword ? 'input-error' : ''}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                tabIndex={-1}
              >
                <i className={`fas ${showConfirmPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
              </button>
            </div>
            {errors.confirmPassword && (
              <div className="field-error">
                <i className="fas fa-exclamation-circle"></i>
                {errors.confirmPassword}
              </div>
            )}
          </div>

          {/* Submit Error */}
          {errors.submit && (
            <div className="error-message">
              <i className="fas fa-exclamation-circle"></i>
              {errors.submit}
            </div>
          )}

          {/* Success Message */}
          {successMessage && (
            <div className="success-message">
              <i className="fas fa-check-circle"></i>
              {successMessage}
            </div>
          )}

          {/* Submit Button */}
          <button 
            type="submit" 
            className="register-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                <span>Se creeaza contul...</span>
              </>
            ) : (
              <>
                <i className="fas fa-user-plus"></i>
                <span>Creeaza cont</span>
              </>
            )}
          </button>
        </form>

        {/* Login Link */}
        <div className="login-section">
          <p className="login-text">
            Ai deja cont?{' '}
            <Link to="/login" className="login-link">
              Conecteaza-te
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Register

