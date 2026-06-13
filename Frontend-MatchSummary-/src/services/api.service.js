/**
 * Serviciu generic pentru apeluri HTTP
 * Gestioneaza toate request-urile catre API
 */

import API_CONFIG from '../config/api.config'

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.baseURL
    this.timeout = API_CONFIG.timeout
    this.defaultHeaders = { ...API_CONFIG.defaultHeaders }
  }

  /**
   * Creeaza URL-ul complet pentru un endpoint
   */
  buildURL(endpoint) {
    // Daca endpoint-ul este deja un URL complet, il returnam direct
    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
      return endpoint
    }
    
    // Altfel, construim URL-ul folosind baseURL
    const base = this.baseURL.endsWith('/') ? this.baseURL.slice(0, -1) : this.baseURL
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
    return `${base}${path}`
  }

  /**
   * Gestioneaza timeout-ul pentru request-uri
   */
  async fetchWithTimeout(url, options, timeout = this.timeout) {
    const controller = new AbortController()
    const id = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      })
      clearTimeout(id)
      return response
    } catch (error) {
      clearTimeout(id)
      if (error.name === 'AbortError') {
        throw new Error('Request timeout')
      }
      throw error
    }
  }

  /**
   * Proceseaza raspunsul de la API
   */
  async handleResponse(response) {
    const contentType = response.headers.get('content-type')
    
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage
        if (errorData.fields && typeof errorData.fields === 'object') {
          const fieldMessages = Object.entries(errorData.fields)
            .map(([field, message]) => `${field}: ${message}`)
            .join(', ')
          if (fieldMessages) {
            errorMessage = `${errorMessage} (${fieldMessages})`
          }
        }
      } catch (e) {
        try {
          const errorText = await response.text()
          if (errorText) errorMessage = errorText
        } catch (e2) {
          // Ignora eroarea de parsing
        }
      }
      throw new Error(errorMessage)
    }

    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }
    
    return await response.text()
  }

  /**
   * Request GET
   */
  async get(endpoint, options = {}) {
    const url = this.buildURL(endpoint)
    const headers = {
      ...this.defaultHeaders,
      ...options.headers,
    }

    try {
      const response = await this.fetchWithTimeout(url, {
        method: 'GET',
        headers,
        ...options,
      })

      return await this.handleResponse(response)
    } catch (error) {
      console.error('GET request failed:', error)
      throw error
    }
  }

  /**
   * Request POST
   */
  async post(endpoint, data = {}, options = {}) {
    const url = this.buildURL(endpoint)
    const headers = {
      ...this.defaultHeaders,
      ...options.headers,
    }

    try {
      const response = await this.fetchWithTimeout(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
        ...options,
      })

      return await this.handleResponse(response)
    } catch (error) {
      console.error('POST request failed:', error)
      throw error
    }
  }

  /**
   * Request PUT
   */
  async put(endpoint, data = {}, options = {}) {
    const url = this.buildURL(endpoint)
    const headers = {
      ...this.defaultHeaders,
      ...options.headers,
    }

    try {
      const response = await this.fetchWithTimeout(url, {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
        ...options,
      })

      return await this.handleResponse(response)
    } catch (error) {
      console.error('PUT request failed:', error)
      throw error
    }
  }

  /**
   * Request DELETE
   */
  async delete(endpoint, options = {}) {
    const url = this.buildURL(endpoint)
    const headers = {
      ...this.defaultHeaders,
      ...options.headers,
    }

    try {
      const response = await this.fetchWithTimeout(url, {
        method: 'DELETE',
        headers,
        ...options,
      })

      return await this.handleResponse(response)
    } catch (error) {
      console.error('DELETE request failed:', error)
      throw error
    }
  }

  /**
   * Adauga header de autentificare
   */
  setAuthToken(token) {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`
  }

  /**
   * Sterge header de autentificare
   */
  removeAuthToken() {
    delete this.defaultHeaders['Authorization']
  }
}

// Exportam o instanta singleton
export default new ApiService()

