// Rutele folosite de frontend catre backend
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',

  auth: {
    login: '/auth/login',
    register: '/auth/register',
    me: '/users/me',
  },

  superliga: {
    standings: '/api/superliga/standings',
    fixtures: (season) => `/api/superliga/fixtures/${encodeURIComponent(season)}`,
  },

  winProbability: {
    predict: '/predict',
    predictByFixtureId: '/predict/by-fixture-id',
    predictFromApiFootball: '/predict/from-api-football',
    predictFromApiFootballLink: '/predict/from-api-football-link',
    matches: '/matches',
    matchDetails: (matchId) => `/matches/${encodeURIComponent(matchId)}`,
    health: '/health',
  },

  timeout: 30000,

  defaultHeaders: {
    'Content-Type': 'application/json',
  },
}

export default API_CONFIG

