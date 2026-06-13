import React, { useCallback, useEffect, useMemo, useState } from 'react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import Loading from '../components/Loading'
import { superligaService, winProbabilityService } from '../services'
import { useSuperligaStandings } from '../hooks'
import './FixturesListPage.css'

const DEFAULT_SEASON = 2022

// Normalizeaza numele echipei (fara diacritice / case) pentru potrivirea
// dintre numele din clasament si cele din lista de meciuri.
const normalizeTeamName = (name) =>
  String(name || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()

const getFixtureId = (fixture) => fixture?.fixture_id || fixture?.id || fixture?.fixture?.id || null

const getHomeTeam = (fixture) =>
  fixture?.home_team || fixture?.teams?.home?.name || fixture?.home?.name || 'Gazde'

const getAwayTeam = (fixture) =>
  fixture?.away_team || fixture?.teams?.away?.name || fixture?.away?.name || 'Oaspeti'

const getHomeLogo = (fixture) =>
  fixture?.home_logo || fixture?.teams?.home?.logo || fixture?.home?.logo || null

const getAwayLogo = (fixture) =>
  fixture?.away_logo || fixture?.teams?.away?.logo || fixture?.away?.logo || null

const getScore = (fixture) => {
  const home = fixture?.home_goals ?? fixture?.goals_home ?? fixture?.score?.fulltime?.home ?? fixture?.score_home
  const away = fixture?.away_goals ?? fixture?.goals_away ?? fixture?.score?.fulltime?.away ?? fixture?.score_away

  if (!Number.isFinite(Number(home)) || !Number.isFinite(Number(away))) {
    return '-'
  }

  return `${Number(home)} - ${Number(away)}`
}

const getStatus = (fixture) =>
  fixture?.status || fixture?.fixture?.status?.short || fixture?.fixture?.status?.long || 'NS'

const formatDate = (value) => {
  if (!value) return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  return date.toLocaleString('ro-RO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const percentage = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`

const FixturesListPage = () => {
  const [season, setSeason] = useState(DEFAULT_SEASON)
  const [fixtures, setFixtures] = useState([])
  const [selectedTeam, setSelectedTeam] = useState('toate')
  const [loadingFixtures, setLoadingFixtures] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)

  const [selectedFixtureId, setSelectedFixtureId] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [loadingPrediction, setLoadingPrediction] = useState(false)

  const { data: standingsData } = useSuperligaStandings()

  const seasonOptions = useMemo(() => [2022], [])

  // Set normalizat cu echipele din clasament (playoff). Toate filtrarile
  // paginii folosesc aceeasi lista, ca sa fie consistenta cu Analiza Meci.
  const standingsTeamSet = useMemo(() => {
    const set = new Set()
    ;(standingsData || []).forEach((team) => {
      const name = team?.echipa || team?.name
      if (name) set.add(normalizeTeamName(name))
    })
    return set
  }, [standingsData])

  // Doar meciurile in care AMBELE echipe sunt in clasament.
  // Daca inca nu avem clasamentul (se incarca / a esuat), nu filtram.
  const standingsFixtures = useMemo(() => {
    if (standingsTeamSet.size === 0) {
      return fixtures
    }

    return fixtures.filter(
      (fixture) =>
        standingsTeamSet.has(normalizeTeamName(getHomeTeam(fixture))) &&
        standingsTeamSet.has(normalizeTeamName(getAwayTeam(fixture)))
    )
  }, [fixtures, standingsTeamSet])

  const teamOptions = useMemo(() => {
    const names = new Set()
    standingsFixtures.forEach((fixture) => {
      names.add(getHomeTeam(fixture))
      names.add(getAwayTeam(fixture))
    })
    return ['toate', ...Array.from(names).sort((a, b) => a.localeCompare(b, 'ro'))]
  }, [standingsFixtures])

  const filteredFixtures = useMemo(() => {
    if (selectedTeam === 'toate') {
      return standingsFixtures
    }

    return standingsFixtures.filter((fixture) =>
      getHomeTeam(fixture) === selectedTeam || getAwayTeam(fixture) === selectedTeam
    )
  }, [standingsFixtures, selectedTeam])

  // Incarca meciurile (din cache implicit; forceRefresh ocoleste cache-ul)
  const loadFixtures = useCallback(async (forceRefresh = false) => {
    if (forceRefresh) {
      setRefreshing(true)
    } else {
      setLoadingFixtures(true)
    }
    setError(null)

    try {
      const data = await superligaService.getFixtures(season, { forceRefresh })
      const sorted = [...data].sort((a, b) => {
        const da = new Date(a?.date || a?.fixture?.date || 0).getTime()
        const db = new Date(b?.date || b?.fixture?.date || 0).getTime()
        return db - da
      })
      setFixtures(sorted)
    } catch (err) {
      setError(err.message || 'Nu s-a putut incarca lista de meciuri')
      setFixtures([])
    } finally {
      setLoadingFixtures(false)
      setRefreshing(false)
    }
  }, [season])

  // La schimbarea sezonului resetam selectia/filtrul si (re)incarcam din cache
  useEffect(() => {
    setPrediction(null)
    setSelectedFixtureId(null)
    setSelectedTeam('toate')
    loadFixtures(false)
  }, [loadFixtures])

  // Reimprospatare manuala: ocoleste cache-ul si reia din retea
  const handleRefresh = () => {
    loadFixtures(true)
  }

  const loadPredictionForFixture = async (fixture) => {
    const fixtureId = getFixtureId(fixture)
    if (!fixtureId) {
      setError('Meciul selectat nu are fixture_id valid')
      return
    }

    setSelectedFixtureId(fixtureId)
    setLoadingPrediction(true)
    setError(null)

    try {
      let nextPrediction = null

      if (fixture?.has_prediction) {
        nextPrediction = await winProbabilityService.getPredictionDetails(`fixture_${fixtureId}`)
      } else {
        nextPrediction = await winProbabilityService.submitPredictionByFixtureId(fixtureId)

        // Actualizam lista si persistam flag-ul has_prediction si in cache,
        // ca eticheta sa ramana dupa reincarcarea paginii.
        const updated = fixtures.map((item) =>
          getFixtureId(item) !== fixtureId ? item : { ...item, has_prediction: true }
        )
        setFixtures(updated)
        superligaService.writeFixturesCache(season, updated)
      }

      setPrediction(nextPrediction)
    } catch (err) {
      setPrediction(null)
      setError(err.message || 'Nu s-a putut obtine predictia pentru meciul selectat')
    } finally {
      setLoadingPrediction(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="fixtures-page">
        <div className="fixtures-page-header">
          <div>
            <h1>Meciuri Superliga</h1>
            <p>Selecteaza o echipa sau un meci pentru a afisa predictia modelului.</p>
          </div>
          <div className="fixtures-filters">
            <label className="season-select" htmlFor="season-select">
              Sezon
              <select id="season-select" value={season} onChange={(e) => setSeason(Number(e.target.value))}>
                {seasonOptions.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <label className="team-select" htmlFor="team-select">
              Echipa
              <select id="team-select" value={selectedTeam} onChange={(e) => setSelectedTeam(e.target.value)}>
                {teamOptions.map((teamName) => (
                  <option key={teamName} value={teamName}>
                    {teamName === 'toate' ? 'Toate echipele' : teamName}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              className="fixtures-refresh-btn"
              onClick={handleRefresh}
              disabled={loadingFixtures || refreshing}
              title="Reincarca meciurile din retea (ocoleste cache-ul local)"
            >
              {refreshing ? 'Se reimprospateaza...' : 'Reimprospateaza'}
            </button>
          </div>
        </div>

        {error && <div className="fixtures-error">{error}</div>}

        <div className="fixtures-layout">
          <section className="fixtures-list">
            {loadingFixtures ? (
              <Loading />
            ) : filteredFixtures.length === 0 ? (
              <div className="fixtures-empty">Nu exista meciuri disponibile pentru sezonul selectat.</div>
            ) : (
              filteredFixtures.map((fixture) => {
                const fixtureId = getFixtureId(fixture)
                const selected = fixtureId === selectedFixtureId

                return (
                  <button
                    type="button"
                    key={fixtureId || `${getHomeTeam(fixture)}-${getAwayTeam(fixture)}`}
                    className={`fixture-card ${selected ? 'selected' : ''}`}
                    onClick={() => loadPredictionForFixture(fixture)}
                    disabled={loadingPrediction}
                  >
                    <div className="fixture-card-top">
                      <span className="fixture-date">{formatDate(fixture?.date || fixture?.fixture?.date)}</span>
                      <span className={`fixture-status fixture-status-${String(getStatus(fixture)).toLowerCase()}`}>
                        {getStatus(fixture)}
                      </span>
                    </div>
                    <div className="fixture-teams">
                      <strong className="fixture-team">
                        {getHomeLogo(fixture) ? <img className="fixture-team-logo" src={getHomeLogo(fixture)} alt={getHomeTeam(fixture)} /> : null}
                        <span>{getHomeTeam(fixture)}</span>
                      </strong>
                      <span>vs</span>
                      <strong className="fixture-team fixture-team-away">
                        <span>{getAwayTeam(fixture)}</span>
                        {getAwayLogo(fixture) ? <img className="fixture-team-logo" src={getAwayLogo(fixture)} alt={getAwayTeam(fixture)} /> : null}
                      </strong>
                    </div>
                    <div className="fixture-card-bottom">
                      <span>Scor: {getScore(fixture)}</span>
                      {fixture?.has_prediction && <span className="prediction-tag">Predictie existenta</span>}
                    </div>
                  </button>
                )
              })
            )}
          </section>

          <aside className="prediction-panel">
            <h2>Predictie</h2>

            {loadingPrediction ? (
              <Loading />
            ) : !prediction ? (
              <p className="prediction-empty">Selecteaza un meci pentru a vedea predictia.</p>
            ) : (
              <>
                <div className="prediction-main">
                  <div>
                    <span>Rezultat estimat</span>
                    <strong>{prediction?.final_prediction?.predicted_outcome_ro || 'Necunoscut'}</strong>
                  </div>
                  <div>
                    <span>Incredere</span>
                    <strong>{percentage(prediction?.final_prediction?.confidence)}</strong>
                  </div>
                </div>

                <div className="probability-list">
                  <div className="probability-row">
                    <span>Gazde</span>
                    <div className="probability-bar">
                      <div style={{ width: percentage(prediction?.final_prediction?.probabilities?.home_win) }} />
                    </div>
                    <span>{percentage(prediction?.final_prediction?.probabilities?.home_win)}</span>
                  </div>
                  <div className="probability-row">
                    <span>Egal</span>
                    <div className="probability-bar">
                      <div style={{ width: percentage(prediction?.final_prediction?.probabilities?.draw) }} />
                    </div>
                    <span>{percentage(prediction?.final_prediction?.probabilities?.draw)}</span>
                  </div>
                  <div className="probability-row">
                    <span>Oaspeti</span>
                    <div className="probability-bar">
                      <div style={{ width: percentage(prediction?.final_prediction?.probabilities?.away_win) }} />
                    </div>
                    <span>{percentage(prediction?.final_prediction?.probabilities?.away_win)}</span>
                  </div>
                </div>
              </>
            )}
          </aside>
        </div>
      </div>
      <Footer />
    </>
  )
}

export default FixturesListPage
