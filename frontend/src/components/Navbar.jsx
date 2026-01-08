import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import './Navbar.css'

const Navbar = ({ userProfile, showAdminToggle = false, showProfile = true }) => {
  const navigate = useNavigate()
  const { logout } = useApp()

  const handleProfileClick = () => {
    navigate('/profile')
  }

  const handleAdminToggle = () => {
    navigate('/admin')
  }

  return (
    <motion.nav
      className="navbar"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="navbar-container">
        <motion.h1
          className="navbar-heading"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate('/dashboard')}
        >
          Techbank.Ai
        </motion.h1>

        <div className="navbar-actions">
          {showAdminToggle && (
            <button
              className="admin-toggle"
              onClick={handleAdminToggle}
            >
              Admin
            </button>
          )}

          {showProfile && (
            <button
              className="profile-button"
              onClick={handleProfileClick}
            >
              <div className="profile-avatar">
                {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
              </div>
            </button>
          )}

          <button
            className="logout-button-nav"
            onClick={async () => {
              await logout()
              navigate('/')
            }}
            title="Logout"
          >
            Logout
          </button>
        </div>
      </div>
    </motion.nav>
  )
}

export default Navbar

