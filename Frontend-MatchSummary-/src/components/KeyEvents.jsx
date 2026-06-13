import React from 'react'
import './KeyEvents.css'

/**
 * Component pentru afisarea evenimentelor cheie dintr-un meci
 * Include tip (gol/cartonas rosu/turning point), impact, si schimbarea probabilitatii
 */
const KeyEvents = ({ events, favoriteOutcome = 'home_win', homeTeam = 'Gazde', awayTeam = 'Oaspeti' }) => {
  if (!events || events.length === 0) {
    return (
      <div className="key-events">
        <h3 className="events-title">
          <i className="fas fa-list-ul"></i> Key Events
        </h3>
        <p className="no-events">Nu exista evenimente cheie inregistrate.</p>
      </div>
    )
  }

  const getEventIcon = (type) => {
    const icons = {
      goal_home: 'fa-futbol',
      goal_away: 'fa-futbol',
      red_card: 'fa-square',
      yellow_card_home: 'fa-square',
      yellow_card_away: 'fa-square',
      substitution: 'fa-right-left',
      turning_point: 'fa-sync-alt',
      penalty: 'fa-dot-circle',
      var_decision: 'fa-tv'
    }
    return icons[type] || 'fa-exclamation-circle'
  }

  const getEventTypeLabel = (type) => {
    const labels = {
      goal_home: 'Gol Gazde',
      goal_away: 'Gol Oaspeti',
      red_card: 'Cartonas Rosu',
      yellow_card_home: 'Cartonas Galben Gazde',
      yellow_card_away: 'Cartonas Galben Oaspeti',
      substitution: 'Schimbare',
      turning_point: 'Turning Point',
      penalty: 'Penalty',
      var_decision: 'Decizie VAR'
    }
    return labels[type] || type
  }

  const getEventTypeClass = (type) => {
    if (type === 'goal_home') return 'event-type-home'
    if (type === 'goal_away') return 'event-type-away'
    if (type === 'red_card') return 'event-type-red'
    if (type === 'yellow_card_home') return 'event-type-home'
    if (type === 'yellow_card_away') return 'event-type-away'
    if (type === 'turning_point') return 'event-type-turning'
    return 'event-type-neutral'
  }

  const getImpactClass = (impact) => {
    if (!impact) return 'impact-medium'
    const impactLower = impact.toLowerCase()
    if (impactLower === 'critical') return 'impact-critical'
    if (impactLower === 'high') return 'impact-high'
    if (impactLower === 'medium') return 'impact-medium'
    return 'impact-low'
  }

  const getImpactLabel = (impact) => {
    const labels = {
      critical: 'CRITICO',
      high: 'RIDICAT',
      medium: 'MEDIU',
      low: 'SCAZUT'
    }
    return labels[impact?.toLowerCase()] || impact || 'MEDIU'
  }

  const formatProbabilityChange = (change) => {
    if (!change) return null
    const percentage = (Math.abs(change) * 100).toFixed(1)
    const sign = change > 0 ? '+' : '-'
    return `${sign}${percentage}%`
  }

  const formatPct = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`

  const getFavoriteConfig = () => {
    if (favoriteOutcome === 'away_win') {
      return {
        key: 'away_win',
        label: `Victorie ${awayTeam}`,
      }
    }

    if (favoriteOutcome === 'draw') {
      return {
        key: 'draw',
        label: 'Egal',
      }
    }

    return {
      key: 'home_win',
      label: `Victorie ${homeTeam}`,
    }
  }

  const favoriteConfig = getFavoriteConfig()

  return (
    <div className="key-events">
      <h3 className="events-title">
        <i className="fas fa-list-ul"></i> Key Events
      </h3>
      <p className="events-subtitle">
        Momentele decisive care au influentat directia favorita: {favoriteConfig.label}
      </p>

      <div className="events-timeline">
        {events.map((event, index) => {
          const beforeFavorite = Number(event?.before_probabilities?.[favoriteConfig.key] ?? 0)
          const afterFavorite = Number(event?.after_probabilities?.[favoriteConfig.key] ?? 0)
          const favoriteDelta = afterFavorite - beforeFavorite
          const probChange = formatProbabilityChange(favoriteDelta)
          const isPositive = favoriteDelta > 0
          
          return (
            <div key={index} className="event-card">
              {/* Timeline line connector */}
              {index < events.length - 1 && <div className="timeline-connector"></div>}

              {/* Event header */}
              <div className="event-header">
                <div className={`event-icon ${getEventTypeClass(event.type)}`}>
                  <i className={`fas ${getEventIcon(event.type)}`}></i>
                </div>

                <div className="event-meta">
                  <div className="event-time">
                    <i className="fas fa-clock"></i>
                    <span>{event.minute}'</span>
                  </div>
                  {event.score && (
                    <div className="event-score">{event.score}</div>
                  )}
                </div>

                <div className={`impact-badge ${getImpactClass(event.impact)}`}>
                  <i className="fas fa-exclamation-triangle"></i>
                  {getImpactLabel(event.impact)}
                </div>
              </div>

              {/* Event body */}
              <div className="event-body">
                <div className="event-type-label">
                  {getEventTypeLabel(event.type)}
                </div>
                <p className="event-description">{event.description}</p>

                {(event.player || event.team) && (
                  <p className="event-description">
                    {event.player ? `Jucator: ${event.player}` : ''}
                    {event.player && event.team ? ' | ' : ''}
                    {event.team ? `Echipa: ${event.team === 'away' ? 'Oaspeti' : 'Gazde'}` : ''}
                  </p>
                )}

                {/* Probability change indicator */}
                {probChange && (
                  <div className="probability-shift">
                    <div className="shift-label">
                      <i className="fas fa-chart-line"></i>
                      Schimbare probabilitate favorita ({favoriteConfig.label}):
                    </div>
                    <div className={`shift-value ${isPositive ? 'positive' : 'negative'}`}>
                      <i className={`fas fa-arrow-${isPositive ? 'up' : 'down'}`}></i>
                      {probChange}
                    </div>
                  </div>
                )}

                {/* Before/After probability only for favorite direction */}
                {event.before_probabilities && event.after_probabilities && (
                  <div className="probability-comparison">
                    <div className="prob-before">
                      <span className="prob-label">{favoriteConfig.label} (inainte):</span>
                      <span className="prob-value">{formatPct(beforeFavorite)}</span>
                    </div>
                    <i className="fas fa-arrow-right prob-arrow"></i>
                    <div className="prob-after">
                      <span className="prob-label">{favoriteConfig.label} (dupa):</span>
                      <span className="prob-value">{formatPct(afterFavorite)}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default KeyEvents
