import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import './WinProbabilityChart.css'

/**
 * Componenta pentru graficul Win Probability (3 linii: home/draw/away)
 */
const WinProbabilityChart = ({ timeline, matchInfo }) => {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="chart-empty">
        <p>Nu sunt disponibile date pentru grafic</p>
      </div>
    )
  }

  // Transforma datele pentru Recharts (converteste probabilitati in procente)
  const chartData = timeline.map((point, index) => {
    // Calculeaza schimbarea probabilitatii fata de punctul anterior
    let probChange = null
    if (index > 0) {
      const prevHomeProb = timeline[index - 1].probabilities.home_win * 100
      const currentHomeProb = point.probabilities.home_win * 100
      probChange = currentHomeProb - prevHomeProb
    }

    return {
      minute: point.minute,
      'Victorie Gazda': Math.round(point.probabilities.home_win * 100),
      'Egal': Math.round(point.probabilities.draw * 100),
      'Victorie Oaspeti': Math.round(point.probabilities.away_win * 100),
      score: point.score,
      event: point.event || null,
      probChange: probChange,
      rawData: point,
    }
  })

  // Gaseste minutele cand s-au marcat goluri (cand scorul se schimba)
  const goalMinutes = []
  for (let i = 1; i < timeline.length; i++) {
    if (timeline[i].score !== timeline[i - 1].score) {
      goalMinutes.push({
        minute: timeline[i].minute,
        score: timeline[i].score,
      })
    }
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload

      // Determina echipa cu probabilitatea cea mai mare
      const homeProb = data['Victorie Gazda']
      const drawProb = data['Egal']
      const awayProb = data['Victorie Oaspeti']
      const maxProb = Math.max(homeProb, drawProb, awayProb)
      
      let predictedOutcome = 'draw'
      if (homeProb === maxProb) predictedOutcome = 'home'
      else if (awayProb === maxProb) predictedOutcome = 'away'

      // Eticheta pentru eveniment
      const getEventLabel = (event) => {
        const labels = {
          goal_home: 'GOL GAZDA',
          goal_away: 'GOL OASPETI',
          red_card: 'CARTONAS ROSU',
          turning_point: 'TURNING POINT'
        }
        return labels[event] || event
      }

      return (
        <div className="custom-tooltip enhanced">
          <div className="tooltip-header">
            <p className="tooltip-title">
              <i className="fas fa-clock"></i> Minutul {data.minute}'
            </p>
            <p className="tooltip-score">
              <i className="fas fa-futbol"></i> {data.score}
            </p>
          </div>

          {/* Event notification */}
          {data.event && (
            <div className={`tooltip-event ${data.event.includes('home') ? 'event-home' : data.event.includes('away') ? 'event-away' : 'event-neutral'}`}>
              <i className={`fas ${data.event.includes('goal') ? 'fa-futbol' : data.event.includes('red') ? 'fa-square' : 'fa-sync-alt'}`}></i>
              <span>{getEventLabel(data.event)}</span>
            </div>
          )}

          <div className="tooltip-probabilities">
            <div className="prob-row prob-home">
              <span className="prob-label">
                <i className="fas fa-home"></i> Victorie Gazda:
              </span>
              <span className="prob-value">
                {homeProb}%
                {predictedOutcome === 'home' && homeProb > 50 && (
                  <i className="fas fa-trophy prediction-icon"></i>
                )}
              </span>
            </div>
            <div className="prob-row prob-draw">
              <span className="prob-label">
                <i className="fas fa-handshake"></i> Egal:
              </span>
              <span className="prob-value">
                {drawProb}%
                {predictedOutcome === 'draw' && drawProb > 50 && (
                  <i className="fas fa-trophy prediction-icon"></i>
                )}
              </span>
            </div>
            <div className="prob-row prob-away">
              <span className="prob-label">
                <i className="fas fa-plane"></i> Victorie Oaspeti:
              </span>
              <span className="prob-value">
                {awayProb}%
                {predictedOutcome === 'away' && awayProb > 50 && (
                  <i className="fas fa-trophy prediction-icon"></i>
                )}
              </span>
            </div>
          </div>

          {/* Probability change */}
          {data.probChange !== null && Math.abs(data.probChange) > 0.5 && (
            <div className="tooltip-change">
              <i className={`fas fa-arrow-${data.probChange > 0 ? 'up' : 'down'}`}></i>
              <span className={data.probChange > 0 ? 'change-positive' : 'change-negative'}>
                {data.probChange > 0 ? '+' : ''}{data.probChange.toFixed(1)}% (Gazda)
              </span>
            </div>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="win-probability-chart">
      <div className="chart-header">
        <h3>Evolutia Probabilitatii de Victorie</h3>
        {matchInfo && (
          <p className="chart-subtitle">
            {matchInfo.home_team} {matchInfo.final_score} {matchInfo.away_team}
          </p>
        )}
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          <XAxis
            dataKey="minute"
            label={{ value: 'Minutul', position: 'insideBottom', offset: -5 }}
            stroke="#6b7280"
          />
          
          <YAxis
            label={{ value: 'Probabilitate (%)', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            stroke="#6b7280"
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend
            verticalAlign="top"
            height={36}
            iconType="line"
          />
          
          {/* Linii pentru goluri */}
          {goalMinutes.map((goal, index) => (
            <ReferenceLine
              key={`goal-${index}`}
              x={goal.minute}
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `GOL ${goal.score}`,
                position: 'top',
                fill: '#10b981',
                fontSize: 12,
                fontWeight: 'bold',
              }}
            />
          ))}
          
          {/* Linia pentru Victorie Gazda */}
          <Line
            type="monotone"
            dataKey="Victorie Gazda"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6 }}
          />
          
          {/* Linia pentru Egal */}
          <Line
            type="monotone"
            dataKey="Egal"
            stroke="#6b7280"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5 }}
            strokeDasharray="5 5"
          />
          
          {/* Linia pentru Victorie Oaspeti */}
          <Line
            type="monotone"
            dataKey="Victorie Oaspeti"
            stroke="#ef4444"
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {goalMinutes.length > 0 && (
        <div className="chart-legend-goals">
          <i className="fas fa-futbol legend-goal-marker"></i>
          <span className="legend-goal-text">Goluri</span>
        </div>
      )}
    </div>
  )
}

export default WinProbabilityChart
