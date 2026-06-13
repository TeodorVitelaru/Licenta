import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ScrollToTop from './components/ScrollToTop'
import Login from './pages/Login'
import Register from './pages/Register'
import Home from './pages/Home'
import Clasament from './pages/Clasament'
import FixturesListPage from './pages/FixturesListPage'
import AnalizaMeci from './pages/AnalizaMeci'

// Rute accesibile doar dupa autentificare
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

// Rute publice: redirectioneaza spre home daca user-ul e deja logat
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>
  }
  return !isAuthenticated ? children : <Navigate to="/home" replace />
}

const AppRoutes = () => {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />
      <Route path="/" element={<Navigate to="/home" replace />} />
      <Route
        path="/home"
        element={
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        }
      />
      <Route
        path="/clasament"
        element={
          <ProtectedRoute>
            <Clasament />
          </ProtectedRoute>
        }
      />
      <Route
        path="/meciuri"
        element={
          <ProtectedRoute>
            <FixturesListPage />
          </ProtectedRoute>
        }
      />
      <Route path="/genereaza" element={<Navigate to="/meciuri" replace />} />
      <Route
        path="/analiza-meci"
        element={
          <ProtectedRoute>
            <AnalizaMeci />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <ScrollToTop />
        <AppRoutes />
      </Router>
    </AuthProvider>
  )
}

export default App

