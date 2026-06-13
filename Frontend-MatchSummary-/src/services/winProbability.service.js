/**
 * Serviciu pentru Win Probability Model (ML)
 * Gestioneaza predictiile si analiza meciurilor
 */

import apiService from './api.service'
import API_CONFIG from '../config/api.config'

class WinProbabilityService {
  getPredictionDetailsEndpoints(matchId) {
    return [API_CONFIG.winProbability.matchDetails(matchId)]
  }

  resolveChartUrl(chartPath) {
    if (!chartPath || typeof chartPath !== 'string') {
      return null
    }

    if (/^https?:\/\//i.test(chartPath)) {
      return chartPath
    }

    const baseURL = (API_CONFIG.baseURL || '').replace(/\/$/, '')
    const normalizedPath = chartPath.startsWith('/') ? chartPath : `/${chartPath}`
    return `${baseURL}${normalizedPath}`
  }

  normalizeTimelinePoint(point = {}, fallback) {
    const probabilities = point.probabilities || {}
    return {
      minute: Number(point.minute ?? fallback.minute ?? 0),
      timestamp_seconds: Number(point.timestamp_seconds ?? fallback.timestamp_seconds ?? 0),
      score: point.score || fallback.score || '-',
      probabilities: {
        home_win: Number(probabilities.home_win ?? point.home_win ?? fallback.probabilities.home_win ?? 0),
        draw: Number(probabilities.draw ?? point.draw ?? fallback.probabilities.draw ?? 0),
        away_win: Number(probabilities.away_win ?? point.away_win ?? fallback.probabilities.away_win ?? 0),
      },
      predicted_outcome: point.predicted_outcome || fallback.predicted_outcome || 'draw',
      event: point.event || (point.event_type ? this.normalizeEventType(point.event_type, point.team) : null),
    }
  }

  parseTeamsFromMatchId(matchId) {
    if (!matchId || typeof matchId !== 'string') {
      return { home_team: 'Home Team', away_team: 'Away Team' }
    }

    const lowered = matchId.toLowerCase().replace(/^match_/, '')
    const parts = lowered.split('_vs_')
    if (parts.length < 2) {
      return { home_team: 'Home Team', away_team: 'Away Team' }
    }

    const sanitize = (value) => value
      .replace(/_(manual|test|fixture|prediction)(?:_.*)?$/i, '')
      .replace(/_\d{4}(?:_\d{2}){1,5}$/i, '')
      .replace(/_\d{4,}$/i, '')
      .split('_')
      .filter(Boolean)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')

    return {
      home_team: sanitize(parts[0]),
      away_team: sanitize(parts[1]),
    }
  }

  toOutcomeRo(outcome) {
    if (outcome === 'home_win') return 'Victorie Gazda'
    if (outcome === 'away_win') return 'Victorie Oaspeti'
    if (outcome === 'draw') return 'Egal'
    return 'Necunoscut'
  }

  resultFromScore(score) {
    const parts = String(score || '').split('-')
    if (parts.length !== 2) {
      return null
    }

    const home = Number(parts[0])
    const away = Number(parts[1])
    if (!Number.isFinite(home) || !Number.isFinite(away)) {
      return null
    }

    if (home > away) return 'home_win'
    if (away > home) return 'away_win'
    return 'draw'
  }

  toAccuracy(confidence = 0) {
    if (confidence >= 0.8) return 'high'
    if (confidence >= 0.6) return 'medium'
    return 'low'
  }

  toNumber(value, fallback = 0) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : fallback
  }

  toObject(value, fallback = {}) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }

    if (typeof value === 'string') {
      try {
        const parsed = JSON.parse(value)
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          return parsed
        }
      } catch (error) {
        return fallback
      }
    }

    return fallback
  }

  parsePercentOrNumber(value, fallback = 0) {
    if (typeof value === 'string' && value.trim().endsWith('%')) {
      const parsed = Number(value.replace('%', '').trim())
      return Number.isFinite(parsed) ? parsed : fallback
    }

    return this.toNumber(value, fallback)
  }

  statValue(teamStats = [], candidates = []) {
    const normalizedCandidates = candidates.map((candidate) => String(candidate || '').toLowerCase())
    const found = (teamStats || []).find((stat) => normalizedCandidates.includes(String(stat?.type || '').toLowerCase()))
    return found?.value
  }

  normalizeSourceEventType(event = {}) {
    const type = String(event?.event_type || event?.type || '').toLowerCase()
    const detail = String(event?.detail || event?.additional_info || '').toLowerCase()

    if (type.includes('goal')) return 'goal'
    if (type.includes('card') && detail.includes('red')) return 'red_card'
    if (type.includes('card') && detail.includes('yellow')) return 'yellow_card'
    if (type.includes('red_card')) return 'red_card'
    if (type.includes('yellow_card')) return 'yellow_card'
    if (type.includes('subst')) return 'substitution'
    if (type.includes('penalty')) return 'penalty'
    return 'injury'
  }

  isPredictionResponseShape(payload = {}) {
    return Boolean(payload?.probabilities && payload?.predicted_outcome)
  }

  isMatchInputShape(payload = {}) {
    const requiredFields = ['minute', 'score_home', 'score_away', 'match_id']
    return requiredFields.every((field) => field in payload)
  }

  extractApiFootballBundle(rawPayload = {}) {
    const payload = rawPayload?.data && typeof rawPayload.data === 'object' ? rawPayload.data : rawPayload

    if (payload?.fixture && payload?.statistics && Array.isArray(payload?.events)) {
      return {
        fixture: payload.fixture,
        statistics: payload.statistics,
        events: payload.events,
        match_id: payload.match_id,
      }
    }

    return null
  }

  extractFixtureIdFromApiUrl(apiUrl = '') {
    try {
      const parsed = new URL(apiUrl)
      const fixture = parsed.searchParams.get('fixture')
      const id = parsed.searchParams.get('id')
      return fixture || id || null
    } catch (error) {
      return null
    }
  }

  validateApiFootballLink(apiUrl = '') {
    if (!apiUrl || typeof apiUrl !== 'string') {
      return { valid: false, error: 'Link API invalid sau gol' }
    }

    let parsed
    try {
      parsed = new URL(apiUrl)
    } catch (error) {
      return { valid: false, error: 'Link-ul introdus nu este un URL valid' }
    }

    const path = String(parsed.pathname || '').toLowerCase()
    const isAllowedPath = path.includes('/fixtures/events') || path.includes('/fixtures/statistics')
    if (!isAllowedPath) {
      return { valid: false, error: 'Link-ul trebuie sa fie de tip fixtures/events sau fixtures/statistics' }
    }

    const fixtureId = this.extractFixtureIdFromApiUrl(apiUrl)
    if (!fixtureId || !/^\d+$/.test(String(fixtureId))) {
      return { valid: false, error: 'Link-ul trebuie sa contina fixture=<id_numeric>' }
    }

    return { valid: true, fixtureId, normalizedUrl: parsed.toString() }
  }

  async submitPredictionFromApiLink(apiUrl = '', options = {}) {
    const validation = this.validateApiFootballLink(apiUrl)
    if (!validation.valid) {
      throw new Error(validation.error)
    }

    const token = localStorage.getItem('auth_token')
    if (!token) {
      throw new Error('Trebuie sa fii autentificat inainte sa trimiti link-ul API')
    }

    const payload = {
      api_url: validation.normalizedUrl,
      match_id: options?.matchId || '',
    }

    const response = await apiService.post(API_CONFIG.winProbability.predictFromApiFootballLink, payload, {
      ...options,
      headers: {
        ...(options?.headers || {}),
        Authorization: `Bearer ${token}`,
      },
    })
    return this.normalizePredictionResponse(response)
  }

  mapApiFootballBundleToMatchInput(bundle = {}) {
    const fixture = bundle?.fixture || {}
    const statistics = Array.isArray(bundle?.statistics) ? bundle.statistics : []
    const events = Array.isArray(bundle?.events) ? bundle.events : []

    if (!fixture || statistics.length < 2) {
      return null
    }

    const homeTeam = fixture?.teams?.home || {}
    const awayTeam = fixture?.teams?.away || {}

    const homeStats = Array.isArray(statistics?.[0]?.statistics) ? statistics[0].statistics : []
    const awayStats = Array.isArray(statistics?.[1]?.statistics) ? statistics[1].statistics : []

    const minute = this.toNumber(fixture?.status?.elapsed ?? fixture?.elapsed ?? 0, 0)
    const scoreHome = this.toNumber(fixture?.goals?.home ?? fixture?.score_home ?? 0, 0)
    const scoreAway = this.toNumber(fixture?.goals?.away ?? fixture?.score_away ?? 0, 0)

    const inferTeamSide = (sourceEvent) => {
      const sourceTeamId = sourceEvent?.team?.id
      const sourceTeamName = String(sourceEvent?.team?.name || sourceEvent?.team || '').toLowerCase()
      if (sourceTeamId && sourceTeamId === homeTeam?.id) return 'home'
      if (sourceTeamId && sourceTeamId === awayTeam?.id) return 'away'
      if (sourceTeamName && sourceTeamName === String(homeTeam?.name || '').toLowerCase()) return 'home'
      if (sourceTeamName && sourceTeamName === String(awayTeam?.name || '').toLowerCase()) return 'away'
      return 'home'
    }

    const normalizedEvents = events
      .map((sourceEvent) => ({
        minute: this.toNumber(sourceEvent?.time?.elapsed ?? sourceEvent?.minute ?? 0, 0),
        event_type: this.normalizeSourceEventType(sourceEvent),
        team: inferTeamSide(sourceEvent),
        player: sourceEvent?.player?.name || sourceEvent?.player || '',
        additional_info: sourceEvent?.detail || sourceEvent?.comments || sourceEvent?.additional_info || '',
      }))
      .filter((event) => Number.isFinite(Number(event.minute)))
      .sort((a, b) => Number(a.minute) - Number(b.minute))

    const countCards = (teamSide, cardType) => normalizedEvents.filter((event) => event.team === teamSide && event.event_type === cardType).length

    return {
      match_id: bundle?.match_id || `fixture_${fixture?.id || Date.now()}`,
      minute,
      teams: {
        home: {
          id: homeTeam?.id ?? null,
          name: homeTeam?.name || 'Home Team',
          logo: homeTeam?.logo ?? null,
        },
        away: {
          id: awayTeam?.id ?? null,
          name: awayTeam?.name || 'Away Team',
          logo: awayTeam?.logo ?? null,
        },
      },
      score_home: scoreHome,
      score_away: scoreAway,
      xg_home: this.toNumber(this.statValue(homeStats, ['Expected Goals', 'xG']), 0),
      xg_away: this.toNumber(this.statValue(awayStats, ['Expected Goals', 'xG']), 0),
      shots_home: this.toNumber(this.statValue(homeStats, ['Shots', 'Total Shots']), 0),
      shots_away: this.toNumber(this.statValue(awayStats, ['Shots', 'Total Shots']), 0),
      shots_on_target_home: this.toNumber(this.statValue(homeStats, ['Shots on Goal', 'Shots on Target']), 0),
      shots_on_target_away: this.toNumber(this.statValue(awayStats, ['Shots on Goal', 'Shots on Target']), 0),
      passes_home: this.toNumber(this.statValue(homeStats, ['Total Passes', 'Passes']), 0),
      passes_away: this.toNumber(this.statValue(awayStats, ['Total Passes', 'Passes']), 0),
      pressure_home: this.parsePercentOrNumber(this.statValue(homeStats, ['Ball Possession', 'Possession']), 0),
      pressure_away: this.parsePercentOrNumber(this.statValue(awayStats, ['Ball Possession', 'Possession']), 0),
      red_cards_home: countCards('home', 'red_card'),
      red_cards_away: countCards('away', 'red_card'),
      yellow_cards_home: countCards('home', 'yellow_card'),
      yellow_cards_away: countCards('away', 'yellow_card'),
      is_home_team: 1,
      under_pressure: 0,
      counterpress: 0,
      events: normalizedEvents,
    }
  }

  normalizeEventType(eventOrType, explicitTeam = null) {
    const rawType = typeof eventOrType === 'string'
      ? eventOrType
      : (eventOrType?.event_type || eventOrType?.type || 'turning_point')
    const rawTeam = explicitTeam || (typeof eventOrType === 'object' ? eventOrType?.team : null)

    const type = String(rawType || 'turning_point').toLowerCase()
    const team = String(rawTeam || '').toLowerCase()

    if (type === 'goal') return team === 'away' ? 'goal_away' : 'goal_home'
    if (type === 'red_card') return 'red_card'
    if (type === 'yellow_card') return team === 'away' ? 'yellow_card_away' : 'yellow_card_home'
    if (type === 'substitution') return 'substitution'
    if (type === 'penalty') return 'penalty'
    return type || 'turning_point'
  }

  impactFromAbsValue(absImpact = 0) {
    if (absImpact >= 0.3) return 'critical'
    if (absImpact >= 0.12) return 'high'
    if (absImpact >= 0.04) return 'medium'
    return 'low'
  }

  deriveMostVolatilePeriod(timeline = []) {
    if (!Array.isArray(timeline) || timeline.length < 2) {
      return null
    }

    const bucketVolatility = {}

    for (let index = 1; index < timeline.length; index += 1) {
      const current = timeline[index]
      const previous = timeline[index - 1]
      const minute = this.toNumber(current?.minute, 0)

      const bucketStart = Math.floor(minute / 15) * 15
      const bucketEnd = bucketStart + 15
      const bucketKey = `${bucketStart}-${bucketEnd}'`

      const homeDelta = Math.abs(this.toNumber(current?.probabilities?.home_win, 0) - this.toNumber(previous?.probabilities?.home_win, 0))
      const drawDelta = Math.abs(this.toNumber(current?.probabilities?.draw, 0) - this.toNumber(previous?.probabilities?.draw, 0))
      const awayDelta = Math.abs(this.toNumber(current?.probabilities?.away_win, 0) - this.toNumber(previous?.probabilities?.away_win, 0))

      bucketVolatility[bucketKey] = (bucketVolatility[bucketKey] || 0) + homeDelta + drawDelta + awayDelta
    }

    const ranked = Object.entries(bucketVolatility).sort((a, b) => b[1] - a[1])
    return ranked.length > 0 ? ranked[0][0] : null
  }

  deriveDominancePeriods(timeline = []) {
    if (!Array.isArray(timeline) || timeline.length === 0) {
      return []
    }

    const buckets = {}

    timeline.forEach((point) => {
      const minute = this.toNumber(point?.minute, 0)
      const bucketStart = Math.floor(minute / 15) * 15
      const bucketEnd = bucketStart + 15
      const key = `${bucketStart}-${bucketEnd}`

      if (!buckets[key]) {
        buckets[key] = {
          start: bucketStart,
          end: bucketEnd,
          points: [],
        }
      }

      buckets[key].points.push(point)
    })

    return Object.values(buckets)
      .sort((a, b) => a.start - b.start)
      .map((bucket) => {
        const count = bucket.points.length || 1
        const sums = bucket.points.reduce((accumulator, point) => ({
          home: accumulator.home + this.toNumber(point?.probabilities?.home_win, 0),
          draw: accumulator.draw + this.toNumber(point?.probabilities?.draw, 0),
          away: accumulator.away + this.toNumber(point?.probabilities?.away_win, 0),
        }), { home: 0, draw: 0, away: 0 })

        const avg = {
          home_win: sums.home / count,
          draw: sums.draw / count,
          away_win: sums.away / count,
        }

        const maxValue = Math.max(avg.home_win, avg.draw, avg.away_win)
        const dominantTeam = Math.abs(avg.home_win - avg.away_win) < 0.03 && Math.abs(avg.home_win - avg.draw) < 0.03
          ? 'balanced'
          : (maxValue === avg.home_win ? 'home' : (maxValue === avg.away_win ? 'away' : 'balanced'))

        return {
          period: `${bucket.start}-${bucket.end}'`,
          dominant_team: dominantTeam,
          avg_probabilities: avg,
        }
      })
  }

  deriveGoalsBreakdown(keyEvents = [], finalScore = '-', response = {}) {
    const parseScore = (scoreValue) => {
      const scoreText = String(scoreValue || '')
      const match = scoreText.match(/(\d+)\D+(\d+)/)
      if (!match) {
        return null
      }

      return {
        home: this.toNumber(match[1], 0),
        away: this.toNumber(match[2], 0),
      }
    }

    const fromExplicitFields = {
      home: this.toNumber(
        response?.match_info?.home_goals ?? response?.home_goals ?? response?.score_home,
        NaN
      ),
      away: this.toNumber(
        response?.match_info?.away_goals ?? response?.away_goals ?? response?.score_away,
        NaN
      ),
    }

    if (Number.isFinite(fromExplicitFields.home) && Number.isFinite(fromExplicitFields.away)) {
      return {
        total: fromExplicitFields.home + fromExplicitFields.away,
        breakdown: {
          home: fromExplicitFields.home,
          away: fromExplicitFields.away,
        },
      }
    }

    const parsedScore = parseScore(finalScore)
    if (parsedScore) {
      return {
        total: parsedScore.home + parsedScore.away,
        breakdown: parsedScore,
      }
    }

    const breakdown = { home: 0, away: 0 }

    keyEvents.forEach((event) => {
      if (!String(event?.type || '').startsWith('goal')) {
        return
      }

      if (event?.team === 'away' || event?.type === 'goal_away') {
        breakdown.away += 1
      } else {
        breakdown.home += 1
      }
    })

    return {
      total: breakdown.home + breakdown.away,
      breakdown,
    }
  }

  buildFinalStatistics(response = {}) {
    const matchInsights = this.toObject(response?.match_insights, {})
    const rawStats = this.toObject(matchInsights?.final_statistics || response?.final_statistics, {})
    const snapshot = this.toObject(response?._input_snapshot || response?.input_snapshot, {})

    const resolveStatValue = (primaryValue, fallbackValue) => {
      const primary = Number(primaryValue)
      const fallback = Number(fallbackValue)
      const hasPrimary = Number.isFinite(primary)
      const hasFallback = Number.isFinite(fallback)

      if (!hasPrimary && hasFallback) {
        return fallback
      }

      if (!hasPrimary) {
        return 0
      }

      // Unele raspunsuri backend trimit final_statistics cu 0 implicit.
      // Daca snapshot-ul are o valoare pozitiva, il preferam pentru afisare.
      if (primary === 0 && hasFallback && fallback > 0) {
        return fallback
      }

      return primary
    }

    const statFromRawOrSnapshot = (rawCandidates = [], snapshotValue = 0) => {
      const primaryCandidate = rawCandidates.find((value) => Number.isFinite(Number(value)))
      return resolveStatValue(primaryCandidate, snapshotValue)
    }

    return {
      xg: {
        home: statFromRawOrSnapshot([rawStats?.xg?.home, rawStats?.xg_home], snapshot?.xg_home),
        away: statFromRawOrSnapshot([rawStats?.xg?.away, rawStats?.xg_away], snapshot?.xg_away),
      },
      shots: {
        home: statFromRawOrSnapshot([rawStats?.shots?.home, rawStats?.shots_home], snapshot?.shots_home),
        away: statFromRawOrSnapshot([rawStats?.shots?.away, rawStats?.shots_away], snapshot?.shots_away),
      },
      shotsOnTarget: {
        home: statFromRawOrSnapshot([
          rawStats?.shotsOnTarget?.home,
          rawStats?.shots_on_target?.home,
          rawStats?.shots_on_target_home,
        ], snapshot?.shots_on_target_home),
        away: statFromRawOrSnapshot([
          rawStats?.shotsOnTarget?.away,
          rawStats?.shots_on_target?.away,
          rawStats?.shots_on_target_away,
        ], snapshot?.shots_on_target_away),
      },
      passes: {
        home: statFromRawOrSnapshot([rawStats?.passes?.home, rawStats?.passes_home], snapshot?.passes_home),
        away: statFromRawOrSnapshot([rawStats?.passes?.away, rawStats?.passes_away], snapshot?.passes_away),
      },
      possession: {
        home: statFromRawOrSnapshot([rawStats?.possession?.home, rawStats?.possession_home], snapshot?.pressure_home),
        away: statFromRawOrSnapshot([rawStats?.possession?.away, rawStats?.possession_away], snapshot?.pressure_away),
      },
      corners: {
        home: statFromRawOrSnapshot([rawStats?.corners?.home, rawStats?.corners_home], snapshot?.corners_home),
        away: statFromRawOrSnapshot([rawStats?.corners?.away, rawStats?.corners_away], snapshot?.corners_away),
      },
    }
  }

  deriveBiggestSwing(keyEvents = []) {
    if (!Array.isArray(keyEvents) || keyEvents.length === 0) {
      return null
    }

    const ranked = [...keyEvents].sort((a, b) => this.toNumber(b?.abs_impact, 0) - this.toNumber(a?.abs_impact, 0))
    const event = ranked[0]
    const afterHome = this.toNumber(event?.probabilities?.home_win, 0)
    const impactHome = this.toNumber(event?.impact_home, 0)
    const beforeHome = afterHome - impactHome

    return {
      minute: this.toNumber(event?.minute, 0),
      change: this.toNumber(event?.abs_impact, Math.abs(impactHome)),
      from_probability: this.toNumber(event?.before_probability, beforeHome),
      to_probability: this.toNumber(event?.after_probability, afterHome),
      description: event?.description_nlp || event?.description || 'Moment decisiv in meci',
      type: event?.type,
    }
  }

  deriveParadox(finalStatistics = {}, finalScore = '-') {
    const [homeGoalsRaw, awayGoalsRaw] = String(finalScore).split('-')
    const homeGoals = this.toNumber(homeGoalsRaw, 0)
    const awayGoals = this.toNumber(awayGoalsRaw, 0)

    const homeXg = this.toNumber(finalStatistics?.xg?.home, 0)
    const awayXg = this.toNumber(finalStatistics?.xg?.away, 0)
    const homeShots = this.toNumber(finalStatistics?.shots?.home, 0)
    const awayShots = this.toNumber(finalStatistics?.shots?.away, 0)

    const awayDominated = awayXg > homeXg * 1.5 && awayShots > homeShots * 1.3
    const homeDominated = homeXg > awayXg * 1.5 && homeShots > awayShots * 1.3

    return (homeGoals > awayGoals && awayDominated) || (awayGoals > homeGoals && homeDominated)
  }

  normalizeMatchInsights(response = {}, keyEvents = [], timeline = [], finalScore = '-') {
    const rawInsights = this.toObject(response?.match_insights, {})
    const finalStatistics = this.buildFinalStatistics(response)
    const goals = this.deriveGoalsBreakdown(keyEvents, finalScore, response)
    const biggestSwing = rawInsights?.biggest_swing || this.deriveBiggestSwing(keyEvents)

    return {
      ...rawInsights,
      timeline_points: this.toNumber(rawInsights?.timeline_points, timeline.length),
      decisive_moments_count: this.toNumber(rawInsights?.decisive_moments_count, keyEvents.length),
      goals_detected: this.toNumber(rawInsights?.goals_detected, goals.total),
      red_cards_detected: this.toNumber(rawInsights?.red_cards_detected, keyEvents.filter((event) => String(event.type).includes('red_card')).length),
      yellow_cards_detected: this.toNumber(rawInsights?.yellow_cards_detected, keyEvents.filter((event) => String(event.type).includes('yellow_card')).length),
      max_impact: this.toNumber(rawInsights?.max_impact, this.toNumber(biggestSwing?.change, 0)),
      max_impact_minute: this.toNumber(rawInsights?.max_impact_minute, this.toNumber(biggestSwing?.minute, 0)),
      biggest_swing: biggestSwing,
      most_volatile_period: rawInsights?.most_volatile_period || this.deriveMostVolatilePeriod(timeline),
      dominance_periods: Array.isArray(rawInsights?.dominance_periods) && rawInsights.dominance_periods.length > 0
        ? rawInsights.dominance_periods
        : this.deriveDominancePeriods(timeline),
      total_goals: this.toNumber(rawInsights?.total_goals, goals.total),
      goals_breakdown: rawInsights?.goals_breakdown || goals.breakdown,
      final_statistics: finalStatistics,
      paradox_detected: Boolean(rawInsights?.paradox_detected ?? this.deriveParadox(finalStatistics, finalScore)),
    }
  }

  normalizeKeyEvents(keyEvents = []) {
    if (!Array.isArray(keyEvents)) {
      return []
    }

    return [...keyEvents]
      .sort((a, b) => Number(a?.minute ?? 0) - Number(b?.minute ?? 0))
      .map((event, index) => {
      if (typeof event === 'string') {
        return {
          minute: null,
          score: '-',
          type: 'turning_point',
          description: event,
          impact: 'medium',
          probability_change: 0,
          id: `event-${index}`,
        }
      }

      return {
        minute: event.minute ?? null,
        score: event.score || '-',
        team: String(event.team || '').toLowerCase() === 'away' ? 'away' : 'home',
        player: event.player || null,
        type: this.normalizeEventType(event),
        event_type: event.event_type || event.type || 'turning_point',
        description: event.description_nlp || event.description || 'Eveniment cheie',
        impact: event.impact || this.impactFromAbsValue(this.toNumber(event.abs_impact, Math.abs(this.toNumber(event.impact_home, 0)))),
        probability_change: this.toNumber(event.probability_change, this.toNumber(event.impact_home, this.toNumber(event.abs_impact, 0))),
        before_probability: Number.isFinite(Number(event.before_probability))
          ? Number(event.before_probability)
          : (Number.isFinite(Number(event.probabilities?.home_win)) && Number.isFinite(Number(event.impact_home))
              ? Number(event.probabilities.home_win) - Number(event.impact_home)
              : undefined),
        after_probability: Number.isFinite(Number(event.after_probability))
          ? Number(event.after_probability)
          : (Number.isFinite(Number(event.probabilities?.home_win))
              ? Number(event.probabilities.home_win)
              : undefined),
        abs_impact: this.toNumber(event.abs_impact, Math.abs(this.toNumber(event.impact_home, 0))),
        impact_home: this.toNumber(event.impact_home, 0),
        impact_draw: this.toNumber(event.impact_draw, 0),
        impact_away: this.toNumber(event.impact_away, 0),
        impact_direction: event.impact_direction || null,
        before_probabilities: {
          home_win: Number.isFinite(Number(event?.before_probabilities?.home_win))
            ? Number(event.before_probabilities.home_win)
            : (Number.isFinite(Number(event?.probabilities?.home_win))
                ? Number(event.probabilities.home_win) - this.toNumber(event.impact_home, 0)
                : 0),
          draw: Number.isFinite(Number(event?.before_probabilities?.draw))
            ? Number(event.before_probabilities.draw)
            : (Number.isFinite(Number(event?.probabilities?.draw))
                ? Number(event.probabilities.draw) - this.toNumber(event.impact_draw, 0)
                : 0),
          away_win: Number.isFinite(Number(event?.before_probabilities?.away_win))
            ? Number(event.before_probabilities.away_win)
            : (Number.isFinite(Number(event?.probabilities?.away_win))
                ? Number(event.probabilities.away_win) - this.toNumber(event.impact_away, 0)
                : 0),
        },
        after_probabilities: {
          home_win: this.toNumber(event?.probabilities?.home_win, 0),
          draw: this.toNumber(event?.probabilities?.draw, 0),
          away_win: this.toNumber(event?.probabilities?.away_win, 0),
        },
        probabilities: event.probabilities,
        id: event.id || `event-${index}`,
      }
      })
  }

  normalizePredictionResponse(response, fallbackMatch = null) {
    const matchId = response?.match_id || fallbackMatch?.match_id || String(Date.now())
    const parsedTeams = this.parseTeamsFromMatchId(matchId)

    const probabilities = response?.final_prediction?.probabilities || response?.probabilities || {
      away_win: 0,
      draw: 0,
      home_win: 0,
    }

    const predictedOutcome = response?.final_prediction?.predicted_outcome || response?.predicted_outcome || 'draw'

    const topLevelScore =
      Number.isFinite(Number(response?.score_home)) && Number.isFinite(Number(response?.score_away))
        ? `${Number(response.score_home)}-${Number(response.score_away)}`
        : null

    const fallbackComputedScore =
      Number.isFinite(Number(fallbackMatch?.score_home)) && Number.isFinite(Number(fallbackMatch?.score_away))
        ? `${Number(fallbackMatch.score_home)}-${Number(fallbackMatch.score_away)}`
        : null

    const finalScore = response?.match_info?.final_score || response?.final_score || topLevelScore || fallbackMatch?.score || fallbackComputedScore || '-'
    const competition = response?.match_info?.competition || fallbackMatch?.competition || 'Superliga Romaniei'
    const rawDate = response?.match_info?.date || fallbackMatch?.date || response?.prediction_time || response?.timestamp || new Date().toISOString()
    const parsedDate = new Date(rawDate)
    const formattedDate = Number.isNaN(parsedDate.getTime())
      ? rawDate
      : parsedDate.toLocaleString('ro-RO')

    const homeTeam =
      response?.match_info?.home_team ||
      response?.teams?.home?.name ||
      response?._input_snapshot?.teams?.home?.name ||
      response?.home_team ||
      fallbackMatch?.home_team ||
      parsedTeams.home_team
    const awayTeam =
      response?.match_info?.away_team ||
      response?.teams?.away?.name ||
      response?._input_snapshot?.teams?.away?.name ||
      response?.away_team ||
      fallbackMatch?.away_team ||
      parsedTeams.away_team
    const homeTeamId = response?.teams?.home?.id ?? response?._input_snapshot?.teams?.home?.id ?? null
    const awayTeamId = response?.teams?.away?.id ?? response?._input_snapshot?.teams?.away?.id ?? null
    const homeTeamLogo = response?.teams?.home?.logo ?? response?._input_snapshot?.teams?.home?.logo ?? null
    const awayTeamLogo = response?.teams?.away?.logo ?? response?._input_snapshot?.teams?.away?.logo ?? null
    const minute = response?.minute ?? fallbackMatch?.minute ?? 0

    const fallbackPoint = {
      minute,
      timestamp_seconds: Number(minute) * 60,
      score: finalScore,
      probabilities,
      predicted_outcome: predictedOutcome,
    }

    const parsedInsights = this.toObject(response?.match_insights, {})

    const timelineSource = Array.isArray(response?.timeline) && response.timeline.length > 0
      ? response.timeline
      : (Array.isArray(parsedInsights?.timeline) ? parsedInsights.timeline : [])

    const timeline = timelineSource.length > 0
      ? [...timelineSource]
          .sort((a, b) => Number(a?.minute ?? 0) - Number(b?.minute ?? 0))
          .map((point) => this.normalizeTimelinePoint(point, fallbackPoint))
      : [
          this.normalizeTimelinePoint(fallbackPoint, fallbackPoint),
        ]

    const normalizedTimeline = timeline.length === 1
      ? [
          this.normalizeTimelinePoint({ ...timeline[0], minute: 0, timestamp_seconds: 0 }, fallbackPoint),
          timeline[0],
        ]
      : timeline

    const normalizedKeyEvents = this.normalizeKeyEvents(response?.key_events)
    const normalizedMatchInsights = this.normalizeMatchInsights(response, normalizedKeyEvents, normalizedTimeline, finalScore)

    const resolvedActualResult =
      response?.match_info?.actual_result ||
      response?.actual_result ||
      fallbackMatch?.actual_result ||
      this.resultFromScore(finalScore) ||
      fallbackMatch?.result ||
      null

    const computedCorrect =
      typeof response?.final_prediction?.correct === 'boolean'
        ? response.final_prediction.correct
        : (resolvedActualResult ? predictedOutcome === resolvedActualResult : null)

    return {
      status: response?.status || 'success',
      match_info: {
        match_id: matchId,
        home_team: homeTeam,
        away_team: awayTeam,
        teams: {
          home: {
            id: homeTeamId,
            name: homeTeam,
            logo: homeTeamLogo,
          },
          away: {
            id: awayTeamId,
            name: awayTeam,
            logo: awayTeamLogo,
          },
        },
        final_score: finalScore,
        actual_result: resolvedActualResult,
        actual_result_ro: response?.match_info?.actual_result_ro || this.toOutcomeRo(resolvedActualResult),
        total_events: response?.match_info?.total_events || response?.match_insights?.timeline_points || response?.key_events?.length || 0,
        competition,
        date: formattedDate,
        minute,
      },
      final_prediction: {
        predicted_outcome: predictedOutcome,
        predicted_outcome_ro: response?.final_prediction?.predicted_outcome_ro || this.toOutcomeRo(predictedOutcome),
        probabilities,
        confidence: response?.final_prediction?.confidence ?? response?.confidence ?? 0,
        correct: computedCorrect,
      },
      key_events: normalizedKeyEvents,
      match_insights: normalizedMatchInsights,
      timeline: normalizedTimeline,
      chart: this.resolveChartUrl(response?.chart),
      timestamp: response?.prediction_time || response?.timestamp || new Date().toISOString(),
    }
  }

  buildFallbackMatchFromInput(matchData = {}) {
    const homeTeam = matchData?.teams?.home?.name
    const awayTeam = matchData?.teams?.away?.name
    const hasNumericScore = Number.isFinite(Number(matchData?.score_home)) && Number.isFinite(Number(matchData?.score_away))

    return {
      match_id: matchData?.match_id,
      home_team: homeTeam,
      away_team: awayTeam,
      score: hasNumericScore ? `${Number(matchData.score_home)}-${Number(matchData.score_away)}` : '-',
      minute: Number(matchData?.minute || 0),
      competition: 'User Predictions',
      date: new Date().toISOString(),
    }
  }

  async waitForBackendChart(matchId, fallbackMatch = null, options = {}) {
    const maxAttempts = Number(options.maxAttempts || 4)
    const delayMs = Number(options.delayMs || 900)
    let latestPrediction = null

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        latestPrediction = await this.getPredictionDetails(matchId, fallbackMatch)
        if (latestPrediction?.chart) {
          return latestPrediction
        }
      } catch (error) {
        if (attempt === maxAttempts) {
          throw error
        }
      }

      if (attempt < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, delayMs))
      }
    }

    return latestPrediction
  }

  normalizeHistoryItem(item) {
    const matchId = item?.match_id || String(Date.now())
    const teams = this.parseTeamsFromMatchId(matchId)
    const confidence = item?.confidence ?? 0
    const homeTeam = item?.home_team || item?.teams?.home?.name || item?._input_snapshot?.teams?.home?.name || teams.home_team
    const awayTeam = item?.away_team || item?.teams?.away?.name || item?._input_snapshot?.teams?.away?.name || teams.away_team

    const computedScore =
      Number.isFinite(Number(item?.score_home)) && Number.isFinite(Number(item?.score_away))
        ? `${Number(item.score_home)}-${Number(item.score_away)}`
        : '-'

    return {
      match_id: matchId,
      date: item?.prediction_time || new Date().toISOString(),
      home_team: homeTeam,
      away_team: awayTeam,
      score: item?.score || computedScore,
      result: item?.predicted_outcome || 'draw',
      competition: item?.competition || 'User Predictions',
      win_probability: item?.win_probability ?? confidence,
      accuracy: item?.accuracy || this.toAccuracy(confidence),
      minute: item?.minute ?? 0,
      prediction_time: item?.prediction_time,
    }
  }

  /**
   * Obtine metricile modelului ML
   * @returns {Promise<Object>} Metrici model (RPS, accuracy, calibration, etc.)
   */
  async getModelMetrics() {
    try {
      const health = await this.checkHealth()
      return {
        status: 'success',
        model_info: {
          model_type: health?.model_loaded ? 'LightGBM' : 'Unknown',
          features_count: 33,
          test_samples: 2446447,
          test_matches: 693,
        },
        metrics: {
          rps: { mean: 0.1431 },
          brier_score: { mean: 0.1472 },
          calibration_error: { mean: 0.0309 },
          accuracy: 0.6565,
        },
        summary: {
          rating: health?.model_loaded ? 'online' : 'degraded',
          interpretation: {
            status: health?.status || 'unknown',
            model_loaded: health?.model_loaded ? 'Model loaded' : 'Model not loaded',
            database_available: health?.database_available ? 'Database available' : 'Database unavailable',
          },
        },
      }
    } catch (error) {
      console.error('Error fetching model metrics:', error)
      throw error
    }
  }

  async checkHealth() {
    return await apiService.get(API_CONFIG.winProbability.health)
  }

  async submitPrediction(matchData) {
    const response = await apiService.post(API_CONFIG.winProbability.predict, matchData)
    const fallbackMatch = this.buildFallbackMatchFromInput(matchData)
    const normalized = this.normalizePredictionResponse(response, fallbackMatch)

    const hasEvents = Array.isArray(matchData?.events) && matchData.events.length > 0
    const matchId = normalized?.match_info?.match_id

    if (!hasEvents || !matchId || normalized?.chart) {
      return normalized
    }

    try {
      const refreshed = await this.waitForBackendChart(matchId, fallbackMatch)
      if (!refreshed) {
        return normalized
      }

      return {
        ...normalized,
        ...refreshed,
        chart: refreshed.chart || normalized.chart,
        timeline: Array.isArray(refreshed.timeline) && refreshed.timeline.length > 0 ? refreshed.timeline : normalized.timeline,
        key_events: Array.isArray(refreshed.key_events) && refreshed.key_events.length > 0 ? refreshed.key_events : normalized.key_events,
        match_insights: refreshed.match_insights || normalized.match_insights,
      }
    } catch (error) {
      return normalized
    }
  }

  async submitPredictionByFixtureId(fixtureId) {
    const fixtureIdNumber = Number(fixtureId)
    if (!Number.isFinite(fixtureIdNumber)) {
      throw new Error('fixture_id invalid')
    }

    const response = await apiService.post(API_CONFIG.winProbability.predictByFixtureId, {
      fixture_id: fixtureIdNumber,
    })

    return this.normalizePredictionResponse(response, {
      match_id: `fixture_${fixtureIdNumber}`,
    })
  }

  async submitPredictionFromExternalSource(rawPayload) {
    if (!rawPayload || typeof rawPayload !== 'object') {
      throw new Error('Payload API invalid sau gol')
    }

    if (this.isPredictionResponseShape(rawPayload)) {
      return this.normalizePredictionResponse(rawPayload)
    }

    if (this.isMatchInputShape(rawPayload)) {
      return await this.submitPrediction(rawPayload)
    }

    const bundle = this.extractApiFootballBundle(rawPayload)
    if (!bundle) {
      throw new Error('Format API neacceptat. Foloseste MatchInput sau formatul fixture/statistics/events.')
    }

    const mappedPayload = this.mapApiFootballBundleToMatchInput(bundle)
    if (!mappedPayload) {
      throw new Error('Nu s-a putut mapa payload-ul API in format MatchInput.')
    }

    try {
      const response = await apiService.post(API_CONFIG.winProbability.predictFromApiFootball, {
        fixture: bundle.fixture,
        statistics: bundle.statistics,
        events: bundle.events,
        match_id: bundle.match_id || mappedPayload.match_id,
      })
      return this.normalizePredictionResponse(response, this.buildFallbackMatchFromInput(mappedPayload))
    } catch (error) {
      return await this.submitPrediction(mappedPayload)
    }
  }

  async getUserPredictions() {
    const response = await apiService.get(API_CONFIG.winProbability.matches)
    const list = Array.isArray(response) ? response : response?.matches || []
    return list.map((item) => this.normalizeHistoryItem(item))
  }

  async getPredictionDetails(matchId, fallbackMatch = null) {
    const endpoints = this.getPredictionDetailsEndpoints(matchId)
    let lastError = null

    for (const endpoint of endpoints) {
      try {
        const response = await apiService.get(endpoint)
        if (import.meta.env.DEV) {
          console.log('[WinProbability] GET matches response', {
            endpoint,
            matchId,
            response,
          })
        }
        return this.normalizePredictionResponse(response, fallbackMatch)
      } catch (error) {
        lastError = error
      }
    }

    throw lastError || new Error('Nu s-au putut incarca detaliile predictiei')
  }

  /**
   * Obtine meciurile pentru o echipa
   * @param {string} teamName - Numele echipei
   * @param {Object} options - Optiuni filtrare (season, limit, etc.)
   * @returns {Promise<Array>} Lista de meciuri
   */
  async getTeamMatches(teamName, options = {}) {
    try {
      const predictions = await this.getUserPredictions()
      const normalizedTeamName = String(teamName || '').toLowerCase()

      const filteredMatches = predictions.filter((match) => {
        const home = String(match.home_team || '').toLowerCase()
        const away = String(match.away_team || '').toLowerCase()
        const matchId = String(match.match_id || '').toLowerCase()
        return home.includes(normalizedTeamName) || away.includes(normalizedTeamName) || matchId.includes(normalizedTeamName)
      })

      const limited = Number.isFinite(Number(options.limit))
        ? filteredMatches.slice(0, Number(options.limit))
        : filteredMatches

      return {
        status: 'success',
        team: teamName,
        matches: limited,
        total: limited.length,
      }
    } catch (error) {
      console.error('Error fetching team matches:', error)
      throw error
    }
  }

}

// Exportam o instanta singleton
export default new WinProbabilityService()
