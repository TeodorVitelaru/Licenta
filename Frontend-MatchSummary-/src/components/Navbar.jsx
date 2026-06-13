import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

const Navbar = () => {
  const { user, logout } = useAuth()
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/home" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="brand-logo">
              <i className="fas fa-futbol"></i>
              <span className="brand-text">WP</span>
            </div>
          </Link>
        </div>
        <div className="navbar-links">
          <Link 
            to="/home" 
            className={`nav-link ${isActive('/home') ? 'active' : ''}`}
          >
            Home
          </Link>
          <Link 
            to="/clasament" 
            className={`nav-link ${isActive('/clasament') ? 'active' : ''}`}
          >
            Clasament
          </Link>
          <Link 
            to="/analiza-meci" 
            className={`nav-link ${isActive('/analiza-meci') ? 'active' : ''}`}
          >
            Analiza Meci
          </Link>
          <Link 
            to="/meciuri" 
            className={`nav-link nav-link-highlight ${isActive('/meciuri') ? 'active-highlight' : ''}`}
          >
            Meciuri
          </Link>
        </div>
        <div className="navbar-user">
          <span className="user-name">{user?.name || user?.full_name || user?.email || 'Utilizator'}</span>
          <button className="logout-button" onClick={logout}>
            Deconectare
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar

