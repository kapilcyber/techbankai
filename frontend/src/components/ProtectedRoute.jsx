import { Navigate, useLocation } from 'react-router-dom'
import { useApp } from '../context/AppContext'

const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, userProfile } = useApp()
  const location = useLocation()

  if (!isAuthenticated) {
    // Redirect to login with the attempted location
    const searchParams = adminOnly ? '?admin=true' : ''
    return <Navigate to={`/login${searchParams}`} state={{ from: location }} replace />
  }

  if (adminOnly && userProfile?.mode !== 'admin') {
    // If admin access is required but user is not an admin, redirect to login
    return <Navigate to="/login?admin=true" state={{ from: location }} replace />
  }

  return children
}

export default ProtectedRoute
