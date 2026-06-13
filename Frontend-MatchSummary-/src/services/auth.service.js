/**
 * Serviciu pentru autentificare
 * Gestioneaza login, register, logout
 */

import apiService from './api.service'
import API_CONFIG from '../config/api.config'

class AuthService {
  getStoredToken() {
    return localStorage.getItem('auth_token') || localStorage.getItem('authToken')
  }

  saveToken(token) {
    apiService.setAuthToken(token)
    localStorage.setItem('auth_token', token)
    localStorage.setItem('authToken', token)
  }

  /**
   * Login utilizator
   * @param {string} email - Email-ul utilizatorului
   * @param {string} password - Parola
   * @returns {Promise<Object>} { user, token }
   */
  async login(email, password) {
    try {
      const response = await apiService.post(API_CONFIG.auth.login, {
        email,
        password,
      })
      
      if (response.access_token || response.token || response.accessToken) {
        const token = response.access_token || response.token || response.accessToken
        this.saveToken(token)
      }

      try {
        const currentUser = await this.getCurrentUser()
        localStorage.setItem('user', JSON.stringify(currentUser))
      } catch (profileError) {
        console.warn('Could not fetch user profile after login:', profileError)
      }
      
      return response
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  /**
   * Inregistrare utilizator nou
   * @param {Object} userData - { email, password, name, etc. }
   * @returns {Promise<Object>} { user, token }
   */
  async register(userData) {
    try {
      const payload = {
        email: userData.email,
        password: userData.password,
        full_name: userData.full_name || userData.name || userData.fullName,
      }

      const response = await apiService.post(API_CONFIG.auth.register, payload)
      
      if (response.access_token || response.token || response.accessToken) {
        const token = response.access_token || response.token || response.accessToken
        this.saveToken(token)
      }

      return response
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  /**
   * Logout utilizator
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      // Logout local: sterg token-ul salvat in browser.
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      apiService.removeAuthToken()
      localStorage.removeItem('auth_token')
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
    }
  }

  /**
   * Obtine informatiile utilizatorului curent
   * @returns {Promise<Object>} User data
   */
  async getCurrentUser() {
    try {
      return await apiService.get(API_CONFIG.auth.me)
    } catch (error) {
      console.error('Get current user failed:', error)
      throw error
    }
  }

  /**
   * Refresh token
   * @returns {Promise<Object>} { token }
   */
  async refreshToken() {
    throw new Error('Refresh token endpoint is not configured on backend')
  }

  /**
   * Verifica daca utilizatorul este autentificat
   * @returns {boolean}
   */
  isAuthenticated() {
    const token = this.getStoredToken()
    return !!token
  }

  /**
   * Obtine token-ul din localStorage
   * @returns {string|null}
   */
  getToken() {
    return this.getStoredToken()
  }

  /**
   * Obtine utilizatorul din localStorage
   * @returns {Object|null}
   */
  getUser() {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  }

  /**
   * Initializeaza autentificarea din localStorage
   */
  initAuth() {
    const token = this.getToken()
    if (token) {
      this.saveToken(token)
    }
  }
}

// Exportam o instanta singleton
export default new AuthService()

