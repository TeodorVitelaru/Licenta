import React from 'react'
import './ProbabilityCard.css'

/**
 * Card pentru afisarea probabilitatii unui outcome (home_win/draw/away_win)
 */
const ProbabilityCard = ({ outcome, probability, teamName, isWinner }) => {
  // Configuratie pentru fiecare tip de outcome
  const config = {
    home_win: {
      title: 'Victorie Gazda',
      iconClass: 'fas fa-home',
      colorClass: 'card-home',
    },
    draw: {
      title: 'Egal',
      iconClass: 'fas fa-handshake',
      colorClass: 'card-draw',
    },
    away_win: {
      title: 'Victorie Oaspeti',
      iconClass: 'fas fa-plane',
      colorClass: 'card-away',
    },
  }

  const currentConfig = config[outcome] || config.draw

  // Converteste probabilitatea in procent
  const percentage = probability ? Math.round(probability * 100) : 0

  // Determina nivelul de confidence
  const getConfidenceLevel = (prob) => {
    if (prob >= 0.7) return 'high'
    if (prob >= 0.4) return 'medium'
    return 'low'
  }

  const confidenceLevel = getConfidenceLevel(probability)

  return (
    <div className={`probability-card ${currentConfig.colorClass} ${isWinner ? 'winner' : ''} confidence-${confidenceLevel}`}>
      <div className="card-header">
        <i className={`${currentConfig.iconClass} card-icon`}></i>
        <h4 className="card-title">{currentConfig.title}</h4>
      </div>
      
      <div className="card-content">
        <div className="probability-value">
          {percentage}%
        </div>
        
        {teamName && (
          <div className="team-name">
            {teamName}
          </div>
        )}
        
        {isWinner && (
          <div className="winner-badge">
            <i className="fas fa-trophy trophy-icon"></i>
            <span>FAVORIT</span>
          </div>
        )}
      </div>
      
      <div className="card-footer">
        <div className="confidence-bar">
          <div
            className="confidence-fill"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="confidence-label">
          {confidenceLevel === 'high' && 'Confidence: High'}
          {confidenceLevel === 'medium' && 'Confidence: Medium'}
          {confidenceLevel === 'low' && 'Confidence: Low'}
        </span>
      </div>
    </div>
  )
}

export default ProbabilityCard
