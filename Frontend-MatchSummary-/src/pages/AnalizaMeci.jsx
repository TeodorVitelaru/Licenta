import React, { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import Loading from '../components/Loading'
import MatchCard from '../components/MatchCard'
import WinProbabilityChart from '../components/WinProbabilityChart'
import ProbabilityCard from '../components/ProbabilityCard'
import ModelMetrics from '../components/ModelMetrics'
import MatchInsights from '../components/MatchInsights'
import DominancePeriods from '../components/DominancePeriods'
import KeyEvents from '../components/KeyEvents'
import { useSuperligaStandings } from '../hooks'
import { winProbabilityService } from '../services'
import './AnalizaMeci.css'

const AnalizaMeci = () => {
  const { data: standingsData, loading: loadingStandings } = useSuperligaStandings()
  
  // State management
  const [selectedTeam, setSelectedTeam] = useState('')
  const [teamMatches, setTeamMatches] = useState([])
  const [selectedMatch, setSelectedMatch] = useState(null)
  const [matchPrediction, setMatchPrediction] = useState(null)
  const [modelMetrics, setModelMetrics] = useState(null)
  const [loadingMatches, setLoadingMatches] = useState(false)
  const [loadingPrediction, setLoadingPrediction] = useState(false)
  const [error, setError] = useState(null)
  const [view, setView] = useState('team-select') // 'team-select' | 'match-list' | 'match-detail'

  const renderCorrectnessText = (isCorrect) => {
    if (typeof isCorrect !== 'boolean') {
      return ' N/A'
    }

    return isCorrect ? ' DA' : ' NU'
  }

  // Pregatire lista echipe
  const teams = standingsData && standingsData.length > 0
    ? standingsData.map(team => ({
        name: team.echipa,
        logo: team.logo || team.crest
      }))
    : []

  // Incarca metrici model la mount
  useEffect(() => {
    loadModelMetrics()
  }, [])

  const loadModelMetrics = async () => {
    try {
      const metrics = await winProbabilityService.getModelMetrics()
      setModelMetrics(metrics)
    } catch (err) {
      setError(err.message || 'Nu s-au putut incarca metricile modelului')
      setModelMetrics(null)
    }
  }

  const handleTeamSelect = async (teamName) => {
    setSelectedTeam(teamName)
    setError(null)
    setLoadingMatches(true)
    setView('match-list')

    try {
      const response = await winProbabilityService.getTeamMatches(teamName, { limit: 10 })
      setTeamMatches(response.matches || [])
    } catch (err) {
      setError(err.message || 'Nu s-au putut incarca meciurile echipei selectate')
      setTeamMatches([])
    } finally {
      setLoadingMatches(false)
    }
  }

  const handleMatchSelect = async (match) => {
    setSelectedMatch(match)
    setError(null)
    setLoadingPrediction(true)
    setView('match-detail')

    try {
      const prediction = await winProbabilityService.getPredictionDetails(match.match_id, match)
      setMatchPrediction(prediction)
    } catch (err) {
      setError(err.message || 'Nu s-au putut incarca detaliile predictiei')
      setMatchPrediction(null)
    } finally {
      setLoadingPrediction(false)
    }
  }

  const handleBackToList = () => {
    setView('match-list')
    setSelectedMatch(null)
    setMatchPrediction(null)
  }

  const handleBackToTeamSelect = () => {
    setView('team-select')
    setSelectedTeam('')
    setTeamMatches([])
    setSelectedMatch(null)
    setMatchPrediction(null)
  }

  // Render diferit in functie de view
  const renderContent = () => {
  // Pas 1: alegerea echipei
    if (view === 'team-select') {
      return (
        <div className="team-select-view">
          <div className="view-header">
            <h2>Selecteaza Echipa</h2>
            <p className="view-subtitle">
              Alege echipa ta favorita pentru a vedea analiza meciurilor
            </p>
          </div>

          {loadingStandings ? (
            <Loading />
          ) : (
            <div className="team-grid">
              {teams.map((team) => (
                <div
                  key={team.name}
                  className="team-card"
                  onClick={() => handleTeamSelect(team.name)}
                >
                  {team.logo && (
                    <img src={team.logo} alt={team.name} className="team-logo" />
                  )}
                  <h3 className="team-name">{team.name}</h3>
                  <div className="team-card-footer">
                    <span>Vezi Meciuri →</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }

    // Pas 2: lista meciurilor
    if (view === 'match-list') {
      return (
        <div className="match-list-view">
          <div className="view-header">
            <button className="back-button" onClick={handleBackToTeamSelect}>
              ← Inapoi la Echipe
            </button>
            <h2>Meciurile Echipei {selectedTeam}</h2>
            <p className="view-subtitle">
              Selecteaza un meci pentru a vedea analiza detaliata
            </p>
          </div>

          {loadingMatches ? (
            <Loading />
          ) : teamMatches.length === 0 ? (
            <div className="empty-state">
              <p>Nu sunt disponibile meciuri pentru {selectedTeam}</p>
            </div>
          ) : (
            <div className="matches-grid">
              {teamMatches.map((match) => (
                <MatchCard
                  key={match.match_id}
                  match={match}
                  onClick={handleMatchSelect}
                />
              ))}
            </div>
          )}
        </div>
      )
    }

    // Pas 3: detaliile meciului selectat
    if (view === 'match-detail') {
      return (
        <div className="match-detail-view">
          <div className="view-header">
            <button className="back-button" onClick={handleBackToList}>
              ← Inapoi la Lista Meciuri
            </button>
          </div>

          {loadingPrediction ? (
            <Loading />
          ) : !matchPrediction ? (
            <div className="empty-state">
              <p>Nu sunt disponibile predictii pentru acest meci</p>
            </div>
          ) : (
            <>
              {/* Match Info Header */}
              <div className="match-info-header">
                <h2>
                  {matchPrediction.match_info.home_team} vs {matchPrediction.match_info.away_team}
                </h2>
                <div className="match-meta">
                  <span className="match-score">{matchPrediction.match_info.final_score}</span>
                  <span className="match-date">{matchPrediction.match_info.date}</span>
                  <span className="match-competition">{matchPrediction.match_info.competition}</span>
                </div>
              </div>

              {/* Win Probability Chart */}
              <WinProbabilityChart
                timeline={matchPrediction.timeline}
                matchInfo={matchPrediction.match_info}
              />

              {/* Backend Generated Chart (PNG) */}
              {matchPrediction.chart && (
                <div className="backend-chart-section">
                  <h3 className="section-title">Chart Generat de Backend</h3>
                  <div className="backend-chart-card">
                    <img
                      src={matchPrediction.chart}
                      alt="Win Probability Chart"
                      className="backend-chart-image"
                      loading="lazy"
                    />
                  </div>
                </div>
              )}

              {/* Probability Cards */}
              <div className="probability-cards-section">
                <h3 className="section-title">Predictie Finala</h3>
                <div className="probability-cards-grid">
                  <ProbabilityCard
                    outcome="away_win"
                    probability={matchPrediction.final_prediction.probabilities.away_win}
                    teamName={matchPrediction.match_info.away_team}
                    isWinner={matchPrediction.final_prediction.predicted_outcome === 'away_win'}
                  />
                  <ProbabilityCard
                    outcome="draw"
                    probability={matchPrediction.final_prediction.probabilities.draw}
                    isWinner={matchPrediction.final_prediction.predicted_outcome === 'draw'}
                  />
                  <ProbabilityCard
                    outcome="home_win"
                    probability={matchPrediction.final_prediction.probabilities.home_win}
                    teamName={matchPrediction.match_info.home_team}
                    isWinner={matchPrediction.final_prediction.predicted_outcome === 'home_win'}
                  />
                </div>
              </div>

              {/* Key Events */}
              {matchPrediction.key_events && matchPrediction.key_events.length > 0 && (
                <KeyEvents
                  events={matchPrediction.key_events}
                  favoriteOutcome={matchPrediction.final_prediction.predicted_outcome}
                  homeTeam={matchPrediction.match_info.home_team}
                  awayTeam={matchPrediction.match_info.away_team}
                />
              )}

              {/* Match Insights */}
              {matchPrediction.match_insights && (
                <MatchInsights insights={matchPrediction.match_insights} />
              )}

              {/* Dominance Periods */}
              {matchPrediction.match_insights?.dominance_periods && 
               matchPrediction.match_insights.dominance_periods.length > 0 && (
                <DominancePeriods periods={matchPrediction.match_insights.dominance_periods} />
              )}

              {/* Match Stats */}
              <div className="match-stats-section">
                <h3 className="section-title">Rezultat</h3>
                <div className="result-card">
                  <div className="result-item">
                    <span className="result-label">Rezultat Prezis:</span>
                    <span className="result-value predicted">
                      {matchPrediction.final_prediction.predicted_outcome_ro}
                    </span>
                  </div>
                  <div className="result-item">
                    <span className="result-label">Rezultat Real:</span>
                    <span className="result-value actual">
                      {matchPrediction.match_info.actual_result_ro}
                    </span>
                  </div>
                  <div className="result-item">
                    <span className="result-label">Predictie Corecta:</span>
                    <span className={`result-value ${typeof matchPrediction.final_prediction.correct !== 'boolean' ? 'actual' : (matchPrediction.final_prediction.correct ? 'correct' : 'incorrect')}`}>
                      <i className={`fas ${typeof matchPrediction.final_prediction.correct !== 'boolean' ? 'fa-minus-circle' : (matchPrediction.final_prediction.correct ? 'fa-check-circle' : 'fa-times-circle')}`}></i>
                      {renderCorrectnessText(matchPrediction.final_prediction.correct)}
                    </span>
                  </div>
                  <div className="result-item">
                    <span className="result-label">Confidence:</span>
                    <span className="result-value confidence">
                      {Math.round(matchPrediction.final_prediction.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Model Metrics */}
              {modelMetrics && <ModelMetrics metrics={modelMetrics} />}
            </>
          )}
        </div>
      )
    }

    return null
  }

  return (
    <div className="analiza-meci-container">
      <Navbar />
      <div className="analiza-meci-content">
        <div className="page-header">
          <div className="page-header-content">
            <span className="page-badge">Win Probability Analysis</span>
            <h1>Analiza Meci</h1>
            <p className="page-description">
              Analizeaza meciurile cu ajutorul modelului ML de predictie. 
              Vizualizeaza evolutia probabilitatii de victorie in timp real.
            </p>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <i className="fas fa-exclamation-triangle"></i>
            <p>{error}</p>
          </div>
        )}

        {renderContent()}
      </div>
      <Footer />
    </div>
  )
}

export default AnalizaMeci
