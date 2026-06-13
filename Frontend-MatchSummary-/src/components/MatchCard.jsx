import React from 'react'
import { format } from 'date-fns'
import './MatchCard.css'

/**
 * Card pentru un meci in lista de meciuri
 */
const MatchCard = ({ match, onClick }) => {
  // Formatare data
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString)
      // Formatare simpla fara locale
      const months = ['Ian', 'Feb', 'Mar', 'Apr', 'Mai', 'Iun', 'Iul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      const day = date.getDate()
      const month = months[date.getMonth()]
      const year = date.getFullYear()
      return `${day} ${month} ${year}`
    } catch (e) {
      return dateString
    }
  }

  // Icon pentru rezultat
  const getResultIcon = (result) => {
    if (result === 'home_win' || result === 'away_win') return 'fa-check-circle'
    if (result === 'draw') return 'fa-equals'
    return 'fa-futbol'
  }

  // Clasa CSS pentru badge rezultat
  const getResultClass = (result) => {
    if (result === 'home_win' || result === 'away_win') return 'result-win'
    if (result === 'draw') return 'result-draw'
    return 'result-loss'
  }

  // Label pentru rezultat romanesc
  const getResultLabel = (result) => {
    if (result === 'home_win') return 'Victorie Gazda'
    if (result === 'away_win') return 'Victorie Oaspeti'
    if (result === 'draw') return 'Egal'
    return 'Necunoscut'
  }

  // Clasa pentru accuracy
  const getAccuracyClass = (accuracy) => {
    if (accuracy === 'high') return 'accuracy-high'
    if (accuracy === 'medium') return 'accuracy-medium'
    return 'accuracy-low'
  }

  const accuracyLabel = {
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  }

  return (
    <div className="match-card" onClick={() => onClick(match)}>
      <div className="match-card-header">
        <div className="match-date">
          <i className="fas fa-calendar date-icon"></i>
          <span>{formatDate(match.date)}</span>
        </div>
        <div className={`match-result-badge ${getResultClass(match.result)}`}>
          <i className={`fas ${getResultIcon(match.result)}`}></i>
          <span>{getResultLabel(match.result)}</span>
        </div>
      </div>

      <div className="match-card-teams">
        <div className="team home-team">
          <span className="team-name">{match.home_team}</span>
        </div>
        <div className="match-score">
          {match.score}
        </div>
        <div className="team away-team">
          <span className="team-name">{match.away_team}</span>
        </div>
      </div>

      <div className="match-card-stats">
        <div className="stat">
          <span className="stat-label">Win Probability:</span>
          <span className="stat-value probability">
            {Math.round(match.win_probability * 100)}%
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Accuracy:</span>
          <span className={`stat-value ${getAccuracyClass(match.accuracy)}`}>
            {accuracyLabel[match.accuracy] || 'N/A'}
          </span>
        </div>
      </div>

      <div className="match-card-footer">
        <span className="competition">{match.competition}</span>
        <span className="view-analysis">
          Vezi Analiza Detaliata →
        </span>
      </div>
    </div>
  )
}

export default MatchCard
