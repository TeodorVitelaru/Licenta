import React, { useMemo } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { useAuth } from '../context/AuthContext'
import './Home.css'

const Home = () => {
  const { user } = useAuth()

  // Daca este admin, afiseaza pagina speciala pentru admin
  if (user?.isAdmin) {
    return <AdminHome />
  }

  // Pagina normala pentru utilizatori
  return (
    <div className="home-container">
      <Navbar />
      <div className="home-content">
        {/* Hero Section */}
        <div className="home-hero">
          <div className="hero-content">
            <div className="hero-text">
              <h1>WinProb</h1>
              <p className="hero-subtitle">Predictia in-game a probabilitatii de castig in fotbal</p>
              <p className="hero-description">
                Analiza post-meci care reconstituie evolutia probabilitatilor de victorie folosind Machine Learning. 
                Modelul nostru LightGBM analizeaza 33 de caracteristici ale meciului 
                pentru a estima probabilitati calibrate la fiecare eveniment inregistrat.
              </p>
              <div className="hero-badges">
                <div className="badge badge-primary">
                  <i className="fas fa-bullseye badge-icon"></i>
                  <span>RPS: 0.1431</span>
                </div>
                <div className="badge badge-success">
                  <i className="fas fa-check badge-icon"></i>
                  <span>Brier: 0.1472</span>
                </div>
                <div className="badge badge-info">
                  <i className="fas fa-chart-bar badge-icon"></i>
                  <span>96.9% Calibrare</span>
                </div>
              </div>
              <div className="hero-cta">
                <Link to="/analiza-meci" className="cta-button cta-primary">
                  <span>Analizeaza Meciuri</span>
                  <i className="fas fa-arrow-right"></i>
                </Link>
                <Link to="/clasament" className="cta-button cta-secondary">
                  <span>Vezi Clasament</span>
                </Link>
              </div>
            </div>
            <div className="hero-image">
              <div className="sport-illustration">
                <svg viewBox="0 0 600 450" fill="none" xmlns="http://www.w3.org/2000/svg">
                  {/* Teren de fotbal - fundal */}
                  <rect x="30" y="30" width="540" height="390" fill="url(#fieldGradient)" rx="15"/>
                  
                  {/* Linii teren */}
                  <line x1="300" y1="30" x2="300" y2="420" stroke="white" strokeWidth="4" strokeLinecap="round"/>
                  <circle cx="300" cy="225" r="70" fill="none" stroke="white" strokeWidth="3"/>
                  <circle cx="300" cy="225" r="6" fill="white"/>
                  
                  {/* Zona de penalty stanga */}
                  <rect x="30" y="140" width="80" height="170" fill="none" stroke="white" strokeWidth="3"/>
                  <rect x="30" y="180" width="40" height="90" fill="none" stroke="white" strokeWidth="3"/>
                  
                  {/* Zona de penalty dreapta */}
                  <rect x="490" y="140" width="80" height="170" fill="none" stroke="white" strokeWidth="3"/>
                  <rect x="550" y="180" width="40" height="90" fill="none" stroke="white" strokeWidth="3"/>
                  
                  {/* Jucator 1 - Atacant (albastru) */}
                  <g transform="translate(180, 200)">
                    <circle cx="0" cy="0" r="28" fill="url(#player1Gradient)"/>
                    <ellipse cx="0" cy="35" rx="20" ry="25" fill="url(#player1Gradient)"/>
                    <path d="M-12 -15 L12 -15 L8 25 L-8 25 Z" fill="white" opacity="0.4"/>
                    <circle cx="-8" cy="-8" r="3.5" fill="white"/>
                    <circle cx="8" cy="-8" r="3.5" fill="white"/>
                    <path d="M-6 5 Q0 10 6 5" stroke="white" strokeWidth="2.5" fill="none"/>
                    <line x1="0" y1="0" x2="25" y2="-15" stroke="white" strokeWidth="3" strokeLinecap="round"/>
                  </g>
                  
                  {/* Jucator 2 - Portar (rosu) */}
                  <g transform="translate(480, 225)">
                    <circle cx="0" cy="0" r="28" fill="url(#player2Gradient)"/>
                    <ellipse cx="0" cy="35" rx="20" ry="25" fill="url(#player2Gradient)"/>
                    <path d="M-12 -15 L12 -15 L8 25 L-8 25 Z" fill="white" opacity="0.4"/>
                    <circle cx="-8" cy="-8" r="3.5" fill="white"/>
                    <circle cx="8" cy="-8" r="3.5" fill="white"/>
                    <path d="M-6 5 Q0 10 6 5" stroke="white" strokeWidth="2.5" fill="none"/>
                    <path d="M-15 0 Q-20 -10 -15 -20" stroke="white" strokeWidth="3" strokeLinecap="round" fill="none"/>
                    <path d="M15 0 Q20 -10 15 -20" stroke="white" strokeWidth="3" strokeLinecap="round" fill="none"/>
                  </g>
                  
                  {/* Jucator 3 - Mijlocas (albastru) */}
                  <g transform="translate(250, 280)">
                    <circle cx="0" cy="0" r="24" fill="url(#player1Gradient)"/>
                    <ellipse cx="0" cy="32" rx="18" ry="22" fill="url(#player1Gradient)"/>
                    <path d="M-10 -12 L10 -12 L7 22 L-7 22 Z" fill="white" opacity="0.4"/>
                    <circle cx="-7" cy="-6" r="3" fill="white"/>
                    <circle cx="7" cy="-6" r="3" fill="white"/>
                    <path d="M-5 4 Q0 8 5 4" stroke="white" strokeWidth="2" fill="none"/>
                  </g>
                  
                  {/* Minge - in miscare */}
                  <g transform="translate(320, 190)">
                    <circle cx="0" cy="0" r="18" fill="url(#ballGradient)"/>
                    <path d="M-15 -6 Q0 -10 15 -6 Q15 6 0 10 Q-15 6 -15 -6" stroke="white" strokeWidth="2" fill="none"/>
                    <path d="M-10 0 Q0 -4 10 0 Q10 4 0 8 Q-10 4 -10 0" stroke="white" strokeWidth="2" fill="none"/>
                    <path d="M0 -15 Q-8 -8 -8 0 Q-8 8 0 15 Q8 8 8 0 Q8 -8 0 -15" stroke="white" strokeWidth="1.5" fill="none" opacity="0.7"/>
                    {/* Traiectorie mingii */}
                    <path d="M-30 10 Q-15 5 0 0" stroke="rgba(255,255,255,0.3)" strokeWidth="2" strokeDasharray="4,4" fill="none"/>
                  </g>
                  
                  {/* Gol - cu retea */}
                  <g transform="translate(570, 200)">
                    <rect x="0" y="-30" width="5" height="60" fill="white" opacity="0.8"/>
                    <line x1="0" y1="-30" x2="0" y2="30" stroke="white" strokeWidth="2"/>
                    <line x1="0" y1="-30" x2="-15" y2="-30" stroke="white" strokeWidth="2"/>
                    <line x1="0" y1="30" x2="-15" y2="30" stroke="white" strokeWidth="2"/>
                    <line x1="-15" y1="-30" x2="-15" y2="30" stroke="white" strokeWidth="2"/>
                    {/* Retea gol */}
                    <line x1="0" y1="-25" x2="-12" y2="-25" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="-20" x2="-12" y2="-20" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="-15" x2="-12" y2="-15" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="-10" x2="-12" y2="-10" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="-5" x2="-12" y2="-5" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="0" x2="-12" y2="0" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="5" x2="-12" y2="5" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="10" x2="-12" y2="10" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="15" x2="-12" y2="15" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="20" x2="-12" y2="20" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="0" y1="25" x2="-12" y2="25" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="-3" y1="-30" x2="-3" y2="30" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="-6" y1="-30" x2="-6" y2="30" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="-9" y1="-30" x2="-9" y2="30" stroke="white" strokeWidth="1" opacity="0.5"/>
                    <line x1="-12" y1="-30" x2="-12" y2="30" stroke="white" strokeWidth="1" opacity="0.5"/>
                  </g>
                  
                  {/* AI Symbol - Neural Network (pe teren, colt stanga sus) */}
                  <g transform="translate(80, 80)" opacity="0.8">
                    <circle cx="0" cy="0" r="8" fill="#ff6b35"/>
                    <circle cx="24" cy="0" r="8" fill="#ff6b35"/>
                    <circle cx="48" cy="0" r="8" fill="#ff6b35"/>
                    <circle cx="12" cy="16" r="8" fill="#ff6b35"/>
                    <circle cx="36" cy="16" r="8" fill="#ff6b35"/>
                    <line x1="0" y1="0" x2="12" y2="16" stroke="#ff6b35" strokeWidth="2"/>
                    <line x1="24" y1="0" x2="12" y2="16" stroke="#ff6b35" strokeWidth="2"/>
                    <line x1="24" y1="0" x2="36" y2="16" stroke="#ff6b35" strokeWidth="2"/>
                    <line x1="48" y1="0" x2="36" y2="16" stroke="#ff6b35" strokeWidth="2"/>
                    <line x1="0" y1="0" x2="24" y2="0" stroke="#ff6b35" strokeWidth="2"/>
                    <line x1="24" y1="0" x2="48" y2="0" stroke="#ff6b35" strokeWidth="2"/>
                  </g>
                  
                  {/* Text "AI" discret pe teren */}
                  <text x="95" y="95" fill="#ff6b35" fontSize="14" fontWeight="700" opacity="0.9" fontFamily="Arial, sans-serif">AI</text>
                  
                  <defs>
                    <linearGradient id="fieldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#22c55e"/>
                      <stop offset="50%" stopColor="#16a34a"/>
                      <stop offset="100%" stopColor="#15803d"/>
                    </linearGradient>
                    <linearGradient id="player1Gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#3b82f6"/>
                      <stop offset="100%" stopColor="#2563eb"/>
                    </linearGradient>
                    <linearGradient id="player2Gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#ef4444"/>
                      <stop offset="100%" stopColor="#dc2626"/>
                    </linearGradient>
                    <linearGradient id="ballGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#fbbf24"/>
                      <stop offset="100%" stopColor="#f59e0b"/>
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* AI Technology Section */}
        <div className="ai-tech-section">
          <div className="section-header">
            <div className="ai-header-icon">
              <i className="fas fa-brain"></i>
            </div>
            <h2>Machine Learning Avansat</h2>
            <p>Model de predictie bazat pe LightGBM (Light Gradient Boosting Machine)</p>
          </div>
          <div className="ai-features-grid">
            <div className="ai-feature-card">
              <div className="ai-feature-icon">
                <i className="fas fa-network-wired"></i>
              </div>
              <h3>LightGBM</h3>
              <p>Model antrenat pe 12.2 milioane de evenimente din 3.464 de meciuri StatsBomb, optimizat prin GOSS si EFB</p>
            </div>
            <div className="ai-feature-card">
              <div className="ai-feature-icon">
                <i className="fas fa-chart-line"></i>
              </div>
              <h3>33 Features</h3>
              <p>24 de features de baza (scor, xG, suturi, pase, presiune, cartonase) plus 9 features derivate de momentum si context</p>
            </div>
            <div className="ai-feature-card">
              <div className="ai-feature-icon">
                <i className="fas fa-chess"></i>
              </div>
              <h3>3 Outcome Classes</h3>
              <p>Probabilitati pentru victorie gazda, egal si victorie oaspeti, reconstituite eveniment cu eveniment</p>
            </div>
            <div className="ai-feature-card">
              <div className="ai-feature-icon">
                <i className="fas fa-trophy"></i>
              </div>
              <h3>Performanta Solida</h3>
              <p>RPS 0.1431 si eroare de calibrare 0.0309, cu probabilitati foarte bine calibrate</p>
            </div>
          </div>
        </div>

        {/* How AI Works Section */}
        <div className="ai-section">
          <div className="section-header">
            <h2>Cum functioneaza modelul?</h2>
            <p>Reconstituire post-meci a evolutiei probabilitatii de victorie</p>
          </div>
          <div className="ai-steps">
            <div className="ai-step ai-step-left">
              <div className="step-icon-wrapper">
                <i className="fas fa-database step-icon"></i>
              </div>
              <h3>Colectare Date</h3>
              <p>Sistemul construieste, pentru fiecare eveniment, un snapshot cu 33 de features: scor, xG, suturi, pase, presiune, cartonase si context temporal.</p>
            </div>
            <div className="ai-step ai-step-center">
              <div className="step-icon-wrapper">
                <i className="fas fa-cogs step-icon"></i>
              </div>
              <h3>Procesare ML</h3>
              <p>Modelul LightGBM analizeaza fiecare snapshot si calculeaza probabilitati pentru cele trei rezultate posibile.</p>
            </div>
            <div className="ai-step ai-step-right">
              <div className="step-icon-wrapper">
                <i className="fas fa-chart-area step-icon"></i>
              </div>
              <h3>Vizualizare</h3>
              <p>Grafice interactive afiseaza traiectoria probabilistica pe tot parcursul meciului si marcheaza momentele decisive.</p>
            </div>
          </div>
        </div>

        {/* Model Performance Gallery */}
        <div className="football-gallery">
          <div className="section-header">
            <h2>Metrici de Performanta</h2>
            <p>Modelul nostru depaseste standardele academice</p>
          </div>
          <div className="gallery-grid">
            <div className="gallery-item">
              <div className="gallery-icon">
                <i className="fas fa-bullseye"></i>
              </div>
              <h3>RPS: 0.1431</h3>
              <p>Ranked Probability Score - metrica principala de evaluare</p>
            </div>
            <div className="gallery-item">
              <div className="gallery-icon">
                <i className="fas fa-percentage"></i>
              </div>
              <h3>Brier: 0.1472</h3>
              <p>Eroarea medie patratica a probabilitatilor prezise</p>
            </div>
            <div className="gallery-item">
              <div className="gallery-icon">
                <i className="fas fa-balance-scale"></i>
              </div>
              <h3>Calibrare: 96.9%</h3>
              <p>Eroare de calibrare 0.0309, sub pragul academic de 0.05</p>
            </div>
            <div className="gallery-item">
              <div className="gallery-icon">
                <i className="fas fa-futbol"></i>
              </div>
              <h3>3.464 Meciuri</h3>
              <p>Set de date StatsBomb, ligile majore europene 2017-2023</p>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="features-section">
          <div className="section-header">
            <h2>Functionalitati Principale</h2>
            <p>Exploreaza analiza predictiva a meciurilor</p>
          </div>
          <div className="home-features">
            <Link to="/clasament" className="home-feature feature-left" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="feature-icon-wrapper">
                <i className="fas fa-trophy feature-icon-large"></i>
              </div>
              <h3>Clasament</h3>
              <p>Vezi clasamentul echipelor din Superliga Romaniei cu statistici detaliate, golaveraj si puncte actualizate.</p>
            </Link>
            <Link to="/analiza-meci" className="home-feature feature-center highlight" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="feature-icon-wrapper">
                <i className="fas fa-chart-line feature-icon-large"></i>
              </div>
              <h3>Analiza Meci</h3>
              <p>Predictii Win Probability in timp real. Selecteaza echipa si meciul pentru analiza detaliata cu grafice interactive.</p>
            </Link>
            <Link to="/meciuri" className="home-feature feature-right" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="feature-icon-wrapper">
                <i className="fas fa-history feature-icon-large"></i>
              </div>
              <h3>Meciuri</h3>
              <p>Acceseaza meciuri anterioare si compara predictiile modelului cu rezultatele reale. Invata din istorie!</p>
            </Link>
          </div>
        </div>

        {/* Benefits Section */}
        <div className="benefits-section">
          <div className="benefits-grid">
            <div className="benefit-card benefit-card-1">
              <div className="benefit-icon-wrapper">
                <i className="fas fa-bolt benefit-icon"></i>
              </div>
              <h3>Eveniment cu Eveniment</h3>
              <p>Probabilitati reconstituite la fiecare eveniment inregistrat al meciului</p>
            </div>
            <div className="benefit-card benefit-card-2">
              <div className="benefit-icon-wrapper">
                <i className="fas fa-microscope benefit-icon"></i>
              </div>
              <h3>Stiintific</h3>
              <p>Bazat pe cercetare academica si metrici validate</p>
            </div>
            <div className="benefit-card benefit-card-3">
              <div className="benefit-icon-wrapper">
                <i className="fas fa-chart-pie benefit-icon"></i>
              </div>
              <h3>Vizual</h3>
              <p>Grafice interactive si intuitive pentru intelegere usoara</p>
            </div>
            <div className="benefit-card benefit-card-4">
              <div className="benefit-icon-wrapper">
                <i className="fas fa-brain benefit-icon"></i>
              </div>
              <h3>Inteligent</h3>
              <p>Model ML antrenat pe milioane de evenimente</p>
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="stats-section">
          <div className="home-stat-item">
            <div className="home-stat-number">12.2M+</div>
            <div className="home-stat-label">Evenimente analizate</div>
          </div>
          <div className="home-stat-item">
            <div className="home-stat-number">3.464</div>
            <div className="home-stat-label">Meciuri in dataset</div>
          </div>
          <div className="home-stat-item">
            <div className="home-stat-number">33</div>
            <div className="home-stat-label">Features ML</div>
          </div>
          <div className="home-stat-item">
            <div className="home-stat-number">0.1431</div>
            <div className="home-stat-label">RPS Score</div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

// Pagina Home speciala pentru Admin
const AdminHome = () => {
  // Informatii despre modelul ML si setul de date
  const stats = {
    datasetMatches: '3.464',
    datasetEvents: '12.2M',
    rps: '0.1431',
    modelName: 'LightGBM'
  }

  return (
    <div className="admin-home-container">
      <Navbar />
      <div className="admin-home-content">
        {/* Welcome Section */}
        <div className="admin-welcome">
          <div className="admin-welcome-content">
            <div className="admin-welcome-icon">
              <i className="fas fa-user-shield"></i>
            </div>
            <div>
              <h1>Panou de Control Admin</h1>
              <p className="admin-welcome-subtitle">
                Bine ai venit in panoul de administrare. Monitorizeaza modelul ML, utilizatorii si analiza meciurilor.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="admin-quick-stats">
          <div className="admin-stat-card admin-stat-primary">
            <div className="admin-stat-icon">
              <i className="fas fa-futbol"></i>
            </div>
            <div className="admin-stat-content">
              <h3>Meciuri in Dataset</h3>
              <p className="admin-stat-value">{stats.datasetMatches}</p>
              <span className="admin-stat-label">StatsBomb 2017-2023</span>
            </div>
          </div>

          <Link to="/analiza-meci" className="admin-stat-card admin-stat-success">
            <div className="admin-stat-icon">
              <i className="fas fa-brain"></i>
            </div>
            <div className="admin-stat-content">
              <h3>Model</h3>
              <p className="admin-stat-value">{stats.modelName}</p>
              <span className="admin-stat-label">Analizeaza un meci</span>
            </div>
            <div className="admin-stat-arrow">
              <i className="fas fa-arrow-right"></i>
            </div>
          </Link>

          <div className="admin-stat-card admin-stat-info">
            <div className="admin-stat-icon">
              <i className="fas fa-bullseye"></i>
            </div>
            <div className="admin-stat-content">
              <h3>RPS Score</h3>
              <p className="admin-stat-value">{stats.rps}</p>
              <span className="admin-stat-label">Metrica principala</span>
            </div>
          </div>
        </div>

        {/* Model Info */}
        <div className="admin-recent-activity">
          <div className="admin-section-header">
            <h2>
              <i className="fas fa-cog"></i>
              Informatii Model
            </h2>
          </div>
          <div className="model-info-grid">
            <div className="model-info-card">
              <div className="model-info-label">Algoritm</div>
              <div className="model-info-value">{stats.modelName}</div>
            </div>
            <div className="model-info-card">
              <div className="model-info-label">RPS Score</div>
              <div className="model-info-value excellent">0.1431</div>
            </div>
            <div className="model-info-card">
              <div className="model-info-label">Calibrare</div>
              <div className="model-info-value excellent">96.9%</div>
            </div>
            <div className="model-info-card">
              <div className="model-info-label">Features</div>
              <div className="model-info-value">33</div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="admin-quick-actions">
          <div className="admin-section-header">
            <h2>
              <i className="fas fa-bolt"></i>
              Actiuni Rapide
            </h2>
          </div>
          <div className="admin-actions-grid">
            <Link to="/statistici" className="admin-action-card">
              <div className="admin-action-icon">
                <i className="fas fa-chart-bar"></i>
              </div>
              <h3>Vezi Statistici</h3>
              <p>Analizeaza datele utilizatorilor si performanta modelului</p>
            </Link>
            <Link to="/analiza-meci" className="admin-action-card">
              <div className="admin-action-icon">
                <i className="fas fa-brain"></i>
              </div>
              <h3>Analiza Meciuri</h3>
              <p>Testeaza predictiile modelului pe meciuri istorice</p>
            </Link>
            <Link to="/clasament" className="admin-action-card">
              <div className="admin-action-icon">
                <i className="fas fa-table"></i>
              </div>
              <h3>Clasament Echipe</h3>
              <p>Urmareste clasamentul actual al Superligii</p>
            </Link>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default Home
