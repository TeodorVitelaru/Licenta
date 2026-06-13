import React, { createContext, useState, useContext, useEffect, useCallback } from 'react'
import { authService } from '../services'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  const hydrateUserFromToken = useCallback(async () => {
    const token = authService.getToken()
    if (!token) {
      setUser(null)
      setIsAuthenticated(false)
      return
    }

    try {
      authService.initAuth()
      const profile = await authService.getCurrentUser()
      const normalizedUser = {
        id: profile.user_id,
        email: profile.email,
        name: profile.full_name || profile.name || profile.email,
        full_name: profile.full_name,
        total_predictions: profile.total_predictions || 0,
        isAdmin: false,
      }
      setUser(normalizedUser)
      setIsAuthenticated(true)
      localStorage.setItem('user', JSON.stringify(normalizedUser))
    } catch (error) {
      console.error('Session restore failed:', error)
      setUser(null)
      setIsAuthenticated(false)
      localStorage.removeItem('auth_token')
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
    }
  }, [])

  const login = async (email, password) => {
    try {
      await authService.login(email, password)
      const profile = await authService.getCurrentUser()

      const userData = {
        id: profile.user_id,
        email: profile.email,
        name: profile.full_name || profile.name || profile.email,
        full_name: profile.full_name,
        total_predictions: profile.total_predictions || 0,
        isAdmin: false,
      }

      setUser(userData)
      setIsAuthenticated(true)
      localStorage.setItem('user', JSON.stringify(userData))
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message || 'Email sau parola incorecta' }
    }
  }

  const register = async (userData) => {
    try {
      await authService.register({
        email: userData.email,
        password: userData.password,
        full_name: userData.full_name || userData.name,
      })

      // Cerinta UX: dupa register trimitem user-ul la login.
      await authService.logout()

      return { success: true, message: 'Contul a fost creat cu succes! Te poti conecta acum.' }
    } catch (error) {
      return { success: false, error: error.message || 'Eroare la inregistrare' }
    }
  }

  const logout = () => {
    authService.logout()
    setUser(null)
    setIsAuthenticated(false)
    localStorage.removeItem('user')
  }

  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await hydrateUserFromToken()
      setLoading(false)
    }
    init()
  }, [hydrateUserFromToken])

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

