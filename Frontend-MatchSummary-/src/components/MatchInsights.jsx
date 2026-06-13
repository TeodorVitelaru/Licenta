import React from 'react'
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar } from 'recharts'
import './MatchInsights.css'

/**
 * Component pentru afisarea insights-urilor despre meci
 * Biggest Swing, Statistics, Volatile Period, etc.
 */
const MatchInsights = ({ insights }) => {
  if (!insights) return null

  const { biggest_swing, final_statistics, most_volatile_period, paradox_detected } = insights

  const statChartData = final_statistics ? [
    {
      name: 'xG',
      home: Number(final_statistics?.xg?.home || 0),
      away: Number(final_statistics?.xg?.away || 0),
    },
    {
      name: 'Shots',
      home: Number(final_statistics?.shots?.home || 0),
      away: Number(final_statistics?.shots?.away || 0),
    },
    {
      name: 'On Target',
      home: Number(final_statistics?.shotsOnTarget?.home || 0),
      away: Number(final_statistics?.shotsOnTarget?.away || 0),
    },
    {
      name: 'Passes',
      home: Number(final_statistics?.passes?.home || 0),
      away: Number(final_statistics?.passes?.away || 0),
    },
  ] : []

  // Verifica paradoxul: echipa cu statistici mai bune a pierdut
  const hasParadox = paradox_detected || (
    final_statistics && 
    Number(final_statistics?.xg?.away || 0) > Number(final_statistics?.xg?.home || 0) * 1.5 && 
    Number(final_statistics?.shots?.away || 0) > Number(final_statistics?.shots?.home || 0) * 1.3
  )

  return (
    <div className="match-insights">
      <h3 className="insights-title">
        <i className="fas fa-lightbulb"></i> Match Insights
      </h3>

      <div className="insights-grid">
        {/* Biggest Swing Card */}
        {biggest_swing && (
          <div className="insight-card biggest-swing-card">
            <div className="card-header">
              <i className="fas fa-bolt card-icon"></i>
              <h4>Game Changer</h4>
            </div>
            <div className="card-content">
              <div className="swing-details">
                <div className="detail-row">
                  <span className="label">Minute:</span>
                  <span className="value highlight">{biggest_swing.minute}'</span>
                </div>
                <div className="detail-row">
                  <span className="label">Impact:</span>
                  <span className="value impact-value">
                    {biggest_swing.change > 0 ? '+' : ''}
                    {(biggest_swing.change * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="detail-row">
                  <span className="label">Probability:</span>
                  <span className="value">
                    {(biggest_swing.from_probability * 100).toFixed(0)}% → {(biggest_swing.to_probability * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <p className="swing-description">
                <i className="fas fa-info-circle"></i>
                {biggest_swing.description}
              </p>
            </div>
          </div>
        )}

        {/* Most Volatile Period */}
        {most_volatile_period && (
          <div className="insight-card volatile-period-card">
            <div className="card-header">
              <i className="fas fa-chart-line card-icon"></i>
              <h4>Most Volatile Period</h4>
            </div>
            <div className="card-content">
              <div className="period-badge">
                <i className="fas fa-clock"></i>
                <span className="period-time">{most_volatile_period}</span>
              </div>
              <p className="period-description">
                Perioada cu cele mai multe schimbari in probabilitati
              </p>
            </div>
          </div>
        )}

        {/* Goals Summary */}
        {insights.total_goals !== undefined && (
          <div className="insight-card goals-card">
            <div className="card-header">
              <i className="fas fa-futbol card-icon"></i>
              <h4>Goals Breakdown</h4>
            </div>
            <div className="card-content">
              <div className="goals-summary">
                <div className="goal-stat">
                  <span className="team-label home">Home</span>
                  <span className="goal-count">{insights.goals_breakdown?.home || 0}</span>
                </div>
                <div className="total-goals">
                  <span className="total-label">Total</span>
                  <span className="total-count">{insights.total_goals}</span>
                </div>
                <div className="goal-stat">
                  <span className="team-label away">Away</span>
                  <span className="goal-count">{insights.goals_breakdown?.away || 0}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Final Statistics */}
      {final_statistics && (
        <div className="final-statistics">
          <h4 className="stats-title">
            <i className="fas fa-chart-bar"></i> Match Statistics
          </h4>

          {/* Comparative Chart */}
          <div className="stats-chart-card">
            <h5 className="stats-chart-title">Comparatie Rapida (Home vs Away)</h5>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={statChartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Legend />
                <Bar dataKey="home" name="Home" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="away" name="Away" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

 {/* Paradox Alert */}
          {hasParadox && (
            <div className="paradox-alert">
              <i className="fas fa-exclamation-triangle"></i>
              <div className="alert-content">
                <strong>PARADOX DETECTED</strong>
                <p>Away team dominated statistics (xG, shots) but lost the match! Classic "against the run of play" victory.</p>
              </div>
            </div>
          )}

          <div className="stats-grid">
            {/* Expected Goals (xG) */}
            {final_statistics.xg && (
              <div className="stat-item">
                <div className="stat-header">
                  <span className="stat-label">Expected Goals (xG)</span>
                </div>
                <div className="stat-bars">
                  <div className="stat-bar-row">
                    <span className="team-name">Home</span>
                    <div className="bar-container">
                      <div
                        className="bar bar-home"
                        style={{
                          width: `${(final_statistics.xg.home / (final_statistics.xg.home + final_statistics.xg.away)) * 100}%`
                        }}
                      ></div>
                    </div>
                    <span className="stat-value">{final_statistics.xg.home.toFixed(2)}</span>
                  </div>
                  <div className="stat-bar-row">
                    <span className="team-name">Away</span>
                    <div className="bar-container">
                      <div
                        className="bar bar-away"
                        style={{
                          width: `${(final_statistics.xg.away / (final_statistics.xg.home + final_statistics.xg.away)) * 100}%`
                        }}
                      ></div>
                    </div>
                    <span className="stat-value">{final_statistics.xg.away.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Shots */}
            {final_statistics.shots && (
              <div className="stat-item">
                <div className="stat-header">
                  <span className="stat-label">Shots</span>
                </div>
                <div className="stat-comparison">
                  <div className="stat-side home">
                    <span className="value">{final_statistics.shots.home}</span>
                    <span className="label">Home</span>
                  </div>
                  <div className="stat-divider"></div>
                  <div className="stat-side away">
                    <span className="value">{final_statistics.shots.away}</span>
                    <span className="label">Away</span>
                  </div>
                </div>
              </div>
            )}

            {/* Shots on Target */}
            {final_statistics.shotsOnTarget && (
              <div className="stat-item">
                <div className="stat-header">
                  <span className="stat-label">Shots on Target</span>
                </div>
                <div className="stat-comparison">
                  <div className="stat-side home">
                    <span className="value">{final_statistics.shotsOnTarget.home}</span>
                    <span className="label">Home</span>
                  </div>
                  <div className="stat-divider"></div>
                  <div className="stat-side away">
                    <span className="value">{final_statistics.shotsOnTarget.away}</span>
                    <span className="label">Away</span>
                  </div>
                </div>
              </div>
            )}

            {/* Passing */}
            {final_statistics.passes && (
              <div className="stat-item">
                <div className="stat-header">
                  <span className="stat-label">Passes</span>
                </div>
                <div className="stat-comparison">
                  <div className="stat-side home">
                    <span className="value">{final_statistics.passes.home}</span>
                    <span className="label">Home</span>
                  </div>
                  <div className="stat-divider"></div>
                  <div className="stat-side away">
                    <span className="value">{final_statistics.passes.away}</span>
                    <span className="label">Away</span>
                  </div>
                </div>
              </div>
            )}

            {/* Possession */}
            {final_statistics.possession && (
              <div className="stat-item">
                <div className="stat-header">
                  <span className="stat-label">Possession (%)</span>
                </div>
                <div className="possession-bar">
                  <div
                    className="possession-fill home"
                    style={{ width: `${final_statistics.possession.home}%` }}
                  >
                    <span className="possession-label">{final_statistics.possession.home}%</span>
                  </div>
                  <div
                    className="possession-fill away"
                    style={{ width: `${final_statistics.possession.away}%` }}
                  >
                    <span className="possession-label">{final_statistics.possession.away}%</span>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  )
}

export default MatchInsights
