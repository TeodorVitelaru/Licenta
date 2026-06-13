import React from 'react'
import './DominancePeriods.css'

/**
 * Component pentru afisarea dominantei pe perioade de timp
 * Arata care echipa a dominat in fiecare interval de 15 minute
 */
const DominancePeriods = ({ periods }) => {
  if (!periods || periods.length === 0) return null

  // Gaseste jumatatea (dupa primele 3 perioade de obicei)
  const halfTimeIndex = Math.floor(periods.length / 2)

  return (
    <div className="dominance-periods">
      <h3 className="periods-title">
        <i className="fas fa-clock"></i> Match Timeline - Dominance
      </h3>
      <p className="periods-subtitle">
        Care echipa a controlat jocul in fiecare perioada
      </p>

      <div className="periods-list">
        {periods.map((period, index) => {
          const homeProb = period.avg_probabilities.home_win * 100
          const awayProb = period.avg_probabilities.away_win * 100
          const drawProb = period.avg_probabilities.draw * 100
          const dominant = period.dominant_team

          // Determina care probabilitate este dominanta
          const maxProb = Math.max(homeProb, drawProb, awayProb)
          const dominanceStrength = 
            maxProb > 60 ? 'strong' : 
            maxProb > 45 ? 'moderate' : 
            'balanced'

          return (
            <React.Fragment key={index}>
              <div className={`period-row ${dominanceStrength}`}>
                <div className="period-time">
                  <i className="fas fa-stopwatch"></i>
                  <span>{period.period}</span>
                </div>

                <div className="period-bar">
                  <div
                    className="period-fill away"
                    style={{ width: `${awayProb}%` }}
                    title={`Away: ${awayProb.toFixed(1)}%`}
                  >
                    {awayProb > 12 && (
                      <span className="bar-label">{awayProb.toFixed(0)}%</span>
                    )}
                  </div>
                  <div
                    className="period-fill draw"
                    style={{ width: `${drawProb}%` }}
                    title={`Draw: ${drawProb.toFixed(1)}%`}
                  >
                    {drawProb > 12 && (
                      <span className="bar-label">{drawProb.toFixed(0)}%</span>
                    )}
                  </div>
                  <div
                    className="period-fill home"
                    style={{ width: `${homeProb}%` }}
                    title={`Home: ${homeProb.toFixed(1)}%`}
                  >
                    {homeProb > 12 && (
                      <span className="bar-label">{homeProb.toFixed(0)}%</span>
                    )}
                  </div>
                </div>

                <div className="period-dominant">
                  {dominant === 'home' && (
                    <span className="dominant-badge home">
                      <i className="fas fa-home"></i> Home
                    </span>
                  )}
                  {dominant === 'away' && (
                    <span className="dominant-badge away">
                      <i className="fas fa-plane"></i> Away
                    </span>
                  )}
                  {dominant === 'balanced' && (
                    <span className="dominant-badge balanced">
                      <i className="fas fa-balance-scale"></i> Balanced
                    </span>
                  )}
                </div>
              </div>

              {/* Half-time divider */}
              {index === halfTimeIndex - 1 && (
                <div className="halftime-divider">
                  <hr />
                  <span className="halftime-label">
                    <i className="fas fa-pause-circle"></i> HALF TIME
                  </span>
                  <hr />
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>

      {/* Legend */}
      <div className="periods-legend">
        <div className="legend-item">
          <div className="legend-color home"></div>
          <span>Home Win Probability</span>
        </div>
        <div className="legend-item">
          <div className="legend-color draw"></div>
          <span>Draw Probability</span>
        </div>
        <div className="legend-item">
          <div className="legend-color away"></div>
          <span>Away Win Probability</span>
        </div>
      </div>
    </div>
  )
}

export default DominancePeriods
