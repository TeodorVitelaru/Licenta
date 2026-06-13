/**
 * Serviciu pentru date despre Superliga Romaniei
 * Gestioneaza toate apelurile legate de meciuri, echipe, clasament
 */

import apiService from './api.service'
import API_CONFIG from '../config/api.config'

// Caching meciuri in localStorage - lista de meciuri se schimba rar (sezon istoric),
// iar toate filtrarile din pagina folosesc aceeasi lista cache-uita.
const FIXTURES_CACHE_PREFIX = 'superliga_fixtures'
const FIXTURES_CACHE_VERSION = 'v1'
const FIXTURES_CACHE_TTL_MS = 6 * 60 * 60 * 1000 // 6 ore

class SuperligaService {
  fixturesCacheKey(season) {
    return `${FIXTURES_CACHE_PREFIX}_${FIXTURES_CACHE_VERSION}_${season}`
  }

  /**
   * Citeste meciurile din localStorage.
   * @param {number} season
   * @param {Object} options - { ignoreTtl } pentru a accepta si cache expirat (fallback)
   * @returns {Array|null} lista de meciuri sau null daca nu exista / e expirat
   */
  readFixturesCache(season, { ignoreTtl = false } = {}) {
    try {
      const raw = localStorage.getItem(this.fixturesCacheKey(season))
      if (!raw) return null

      const parsed = JSON.parse(raw)
      if (!parsed || !Array.isArray(parsed.fixtures)) return null

      const isExpired = Date.now() - (parsed.ts || 0) > FIXTURES_CACHE_TTL_MS
      if (isExpired && !ignoreTtl) return null

      return parsed.fixtures
    } catch (error) {
      console.warn('[CACHE] Nu am putut citi meciurile din localStorage:', error)
      return null
    }
  }

  /**
   * Scrie meciurile in localStorage (folosit si pentru a persista has_prediction).
   */
  writeFixturesCache(season, fixtures) {
    try {
      if (!Array.isArray(fixtures)) return
      const payload = JSON.stringify({ ts: Date.now(), season, fixtures })
      localStorage.setItem(this.fixturesCacheKey(season), payload)
    } catch (error) {
      console.warn('[CACHE] Nu am putut salva meciurile in localStorage:', error)
    }
  }

  /**
   * Invalideaza cache-ul de meciuri (pentru un sezon sau toate sezoanele).
   */
  clearFixturesCache(season = null) {
    try {
      if (season != null) {
        localStorage.removeItem(this.fixturesCacheKey(season))
        return
      }

      const prefix = `${FIXTURES_CACHE_PREFIX}_${FIXTURES_CACHE_VERSION}_`
      Object.keys(localStorage)
        .filter((key) => key.startsWith(prefix))
        .forEach((key) => localStorage.removeItem(key))
    } catch (error) {
      console.warn('[CACHE] Nu am putut sterge cache-ul de meciuri:', error)
    }
  }

  normalizeFixturesPayload(payload) {
    if (Array.isArray(payload)) {
      return payload
    }

    if (Array.isArray(payload?.fixtures)) {
      return payload.fixtures
    }

    if (Array.isArray(payload?.data?.fixtures)) {
      return payload.data.fixtures
    }

    return []
  }

  /**
   * Obtine clasamentul
   * Incearca mai multe surse in ordine
   * @param {Object} params - Parametri (sezon, etc.)
   * @returns {Promise<Array>} Clasamentul echipe
   */
  async getStandings(params = {}) {
    try {
      const computedSeason = 2022

      const queryParams = new URLSearchParams({
        ...params,
        season: String(params.season || computedSeason),
      }).toString()

      const endpoint = `${API_CONFIG.superliga.standings}${queryParams ? `?${queryParams}` : ''}`
      const standings = await apiService.get(endpoint)
      return this.transformStandingsData(standings)
    } catch (error) {
      console.error('Error fetching standings:', error)
      throw error
    }
  }

  /**
   * Obtine meciurile pentru un sezon.
   * Foloseste cache din localStorage; reia din retea doar daca lipseste,
   * a expirat sau se cere explicit `forceRefresh`.
   * @param {number} season
   * @param {Object} options - { forceRefresh } pentru a ignora cache-ul
   * @returns {Promise<Array>} lista de meciuri
   */
  async getFixtures(season = 2022, { forceRefresh = false } = {}) {
    const computedSeason = Number.isFinite(Number(season)) ? Number(season) : 2022

    if (!forceRefresh) {
      const cached = this.readFixturesCache(computedSeason)
      if (cached) {
        console.log(`[CACHE] ${cached.length} meciuri servite din localStorage (sezon ${computedSeason})`)
        return cached
      }
    }

    try {
      const endpoint = API_CONFIG.superliga.fixtures(computedSeason)
      const response = await apiService.get(endpoint)
      const fixtures = this.normalizeFixturesPayload(response)
      this.writeFixturesCache(computedSeason, fixtures)
      return fixtures
    } catch (error) {
      console.error('Error fetching fixtures:', error)

      // Fallback: daca reteaua esueaza, incercam cache-ul chiar daca a expirat
      const stale = this.readFixturesCache(computedSeason, { ignoreTtl: true })
      if (stale) {
        console.warn(`[CACHE] Retea indisponibila - folosesc cache expirat (${stale.length} meciuri)`)
        return stale
      }

      throw error
    }
  }

  /**
   * Transforma datele primite in formatul standard
   */
  transformStandingsData(data) {
    // Daca datele sunt deja in formatul corect, le returnam direct
    if (Array.isArray(data) && data.length > 0 && data[0].pozitie) {
      return data
    }
    
    // Altfel, incercam sa transformam din diverse formate
    if (data.standings && Array.isArray(data.standings)) {
      return data.standings[0].table.map((team) => ({
        pozitie: team.position || team.pozitie,
        echipa: team.team?.name || team.name || team.echipa || '',
        meciuri: team.playedGames || team.meciuri || 0,
        victorii: team.won || team.victorii || 0,
        egaluri: team.draw || team.egaluri || 0,
        infrangeri: team.lost || team.infrangeri || 0,
        goluriMarcate: team.goalsFor || team.goluriMarcate || 0,
        goluriPrimite: team.goalsAgainst || team.goluriPrimite || 0,
        golaveraj: team.goalDifference || team.golaveraj || 0,
        puncte: team.points || team.puncte || 0,
      }))
    }
    
    if (Array.isArray(data)) {
      return data.map((team, index) => ({
        pozitie: team.position || team.pozitie || index + 1,
        echipa: team.team?.name || team.name || team.echipa || '',
        meciuri: team.playedGames || team.meciuri || 0,
        victorii: team.won || team.victorii || 0,
        egaluri: team.draw || team.egaluri || 0,
        infrangeri: team.lost || team.infrangeri || 0,
        goluriMarcate: team.goalsFor || team.goluriMarcate || 0,
        goluriPrimite: team.goalsAgainst || team.goluriPrimite || 0,
        golaveraj: team.goalDifference || team.golaveraj || 0,
        puncte: team.points || team.puncte || 0,
      }))
    }
    
    return []
  }
}

// Exportam o instanta singleton
export default new SuperligaService()

