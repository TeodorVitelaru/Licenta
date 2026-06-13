import React from 'react'
import './Footer.css'

const Footer = () => {
  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-section">
          <h3>WinProb</h3>
          <p>Predictia probabilitatii de castig in fotbal folosind Machine Learning, pentru Superliga Romaniei</p>
        </div>
        
        <div className="footer-section">
          <h4>Link-uri rapide</h4>
          <ul>
            <li><a href="/home">Acasa</a></li>
            <li><a href="/clasament">Clasament</a></li>
            <li><a href="/analiza-meci">Analiza Meci</a></li>
            <li><a href="/meciuri">Meciuri</a></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4>Despre</h4>
          <ul>
            <li><a href="#about">Despre noi</a></li>
            <li><a href="#contact">Contact</a></li>
            <li><a href="#privacy">Confidentialitate</a></li>
            <li><a href="#terms">Termeni si conditii</a></li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4>Contact</h4>
          <ul>
            <li>
              <i className="fas fa-envelope"></i>
              <span>contact@winprob.ro</span>
            </li>
            <li>
              <i className="fas fa-phone"></i>
              <span>+40 123 456 789</span>
            </li>
            <li className="social-links">
              <a href="#" aria-label="Facebook">
                <i className="fab fa-facebook"></i>
              </a>
              <a href="#" aria-label="Twitter">
                <i className="fab fa-twitter"></i>
              </a>
              <a href="#" aria-label="Instagram">
                <i className="fab fa-instagram"></i>
              </a>
            </li>
          </ul>
        </div>
      </div>
      
      <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} WinProb. Toate drepturile rezervate.</p>
      </div>
    </footer>
  )
}

export default Footer

