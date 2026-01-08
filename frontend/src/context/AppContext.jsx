import { createContext, useContext, useState, useEffect } from 'react'
import { logout as apiLogout } from '../config/api'

const AppContext = createContext()

export const useApp = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useApp must be used within AppProvider')
  }
  return context
}

export const AppProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    try {
    // Check localStorage for persisted auth state
    // Also verify that userProfile exists to ensure valid session
    const authStatus = localStorage.getItem('isAuthenticated') === 'true'
    const hasProfile = localStorage.getItem('userProfile') !== null
    return authStatus && hasProfile
    } catch (e) {
      console.error('Error accessing localStorage:', e)
      return false
    }
  })
  
  const [userProfile, setUserProfile] = useState(() => {
    try {
    const saved = localStorage.getItem('userProfile')
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch (e) {
        console.error('Error parsing userProfile from localStorage:', e)
        return null
      }
    }
    return null
    } catch (e) {
      console.error('Error accessing localStorage:', e)
      return null
    }
  })
  
  const [selectedEmploymentType, setSelectedEmploymentType] = useState(() => {
    try {
    const saved = localStorage.getItem('selectedEmploymentType')
    return saved ? JSON.parse(saved) : null
    } catch (e) {
      console.error('Error accessing localStorage:', e)
      return null
    }
  })

  // Persist authentication state
  useEffect(() => {
    if (isAuthenticated) {
      localStorage.setItem('isAuthenticated', 'true')
    } else {
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('userProfile')
    }
  }, [isAuthenticated])

  // Persist user profile
  useEffect(() => {
    if (userProfile) {
      localStorage.setItem('userProfile', JSON.stringify(userProfile))
    }
  }, [userProfile])

  // Persist selected employment type
  useEffect(() => {
    if (selectedEmploymentType) {
      localStorage.setItem('selectedEmploymentType', JSON.stringify(selectedEmploymentType))
    } else {
      localStorage.removeItem('selectedEmploymentType')
    }
  }, [selectedEmploymentType])

  const logout = async () => {
    try {
      await apiLogout()
    } catch (error) {
      console.error('Logout error:', error)
      // Continue with local logout even if API call fails
    } finally {
      setIsAuthenticated(false)
      setUserProfile(null)
      setSelectedEmploymentType(null)
      localStorage.clear()
      // Navigate will be handled by App.jsx route protection
    }
  }

  return (
    <AppContext.Provider
      value={{
        isAuthenticated,
        setIsAuthenticated,
        userProfile,
        setUserProfile,
        selectedEmploymentType,
        setSelectedEmploymentType,
        logout,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

