import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { getProfile, updateProfile } from '../config/api'
import Navbar from '../components/Navbar'
import './Profile.css'

const Profile = () => {
  const navigate = useNavigate()
  const { userProfile, logout, setUserProfile } = useApp()
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [editedProfile, setEditedProfile] = useState({
    name: userProfile?.name || '',
    email: userProfile?.email || '',
    phone: userProfile?.phone || '',
    dateOfBirth: userProfile?.dateOfBirth || '',
    role: userProfile?.role || '',
    skills: userProfile?.skills || ''
  })

  useEffect(() => {
    // Load latest profile from backend
    const fetchProfile = async () => {
      try {
        setLoading(true)
        setError('')
        const profile = await getProfile()
        const mergedProfile = {
          ...userProfile,
          id: profile.id,
          name: profile.name,
          email: profile.email,
          mode: profile.mode,
          created_at: profile.created_at || userProfile?.created_at,
        }
        setUserProfile(mergedProfile)
        setEditedProfile({
          name: mergedProfile.name || '',
          email: mergedProfile.email || '',
          phone: mergedProfile.phone || '',
          dateOfBirth: mergedProfile.dateOfBirth || '',
          role: mergedProfile.role || '',
          skills: mergedProfile.skills || ''
        })
      } catch (err) {
        console.error('Error loading profile:', err)
        setError(err.message || 'Failed to load profile')
      } finally {
        setLoading(false)
      }
    }

    // Only fetch if we have a token (user is authenticated)
    fetchProfile()
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      setError('')

      // Prepare data for backend (only fields it knows)
      const payload = {
        name: editedProfile.name,
        dob: editedProfile.dateOfBirth || '',
        // state, city, pincode could be added here later
      }

      const updated = await updateProfile(payload)

      const updatedProfile = {
        ...userProfile,
        ...editedProfile,
        name: updated.name,
        email: updated.email,
        mode: updated.mode || userProfile?.mode,
        created_at: updated.created_at || userProfile?.created_at,
      }

      setUserProfile(updatedProfile)
      setIsEditing(false)
    } catch (err) {
      console.error('Profile save error:', err)
      setError(err.message || 'Failed to save profile')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setEditedProfile({
      name: userProfile?.name || '',
      email: userProfile?.email || '',
      phone: userProfile?.phone || '',
      dateOfBirth: userProfile?.dateOfBirth || '',
      role: userProfile?.role || '',
      skills: userProfile?.skills || ''
    })
    setIsEditing(false)
  }

  const handleChange = (e) => {
    setEditedProfile({
      ...editedProfile,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="profile-container">
      <Navbar userProfile={userProfile} />

      <div className="profile-content">
        {error && (
          <div className="profile-error">
            {error}
          </div>
        )}
        <motion.div
          className="profile-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="profile-header-section">
            <div className="profile-avatar-large">
              {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="profile-header-info">
              <h1>{userProfile?.name || 'User'}</h1>
              <p>{userProfile?.email || 'No email provided'}</p>
              {userProfile?.role && (
                <span className="profile-role">{userProfile.role}</span>
              )}
            </div>
            {!isEditing ? (
              <button className="edit-profile-btn" onClick={handleEdit}>
                {loading ? 'Loading...' : 'Edit Profile'}
              </button>
            ) : (
              <div className="edit-actions-header">
                <button className="save-btn" onClick={handleSave}>
                  Save
                </button>
                <button className="cancel-btn" onClick={handleCancel}>
                  Cancel
                </button>
              </div>
            )}
          </div>

          <div className="profile-divider-main"></div>

          <div className="profile-sections">
            <motion.div
              className="profile-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <h2>Personal Information</h2>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Full Name</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="name"
                      value={editedProfile.name}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your name"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.name || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Email Address</span>
                  {isEditing ? (
                    <input
                      type="email"
                      name="email"
                      value={editedProfile.email}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your email"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.email || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Phone Number</span>
                  {isEditing ? (
                    <input
                      type="tel"
                      name="phone"
                      value={editedProfile.phone}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your phone number"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.phone || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Date of Birth</span>
                  {isEditing ? (
                    <input
                      type="date"
                      name="dateOfBirth"
                      value={editedProfile.dateOfBirth}
                      onChange={handleChange}
                      className="profile-input"
                    />
                  ) : (
                    <span className="info-value">
                      {userProfile?.dateOfBirth
                        ? new Date(userProfile.dateOfBirth).toLocaleDateString()
                        : 'Not set'}
                    </span>
                  )}
                </div>
              </div>
            </motion.div>

            <motion.div
              className="profile-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <h2>Account Information</h2>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">User ID</span>
                  <span className="info-value">{userProfile?.id || 'N/A'}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Member Since</span>
                  <span className="info-value">
                    {userProfile?.createdAt
                      ? new Date(userProfile.createdAt).toLocaleDateString()
                      : new Date().toLocaleDateString()}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Last Login</span>
                  <span className="info-value">
                    {userProfile?.lastLogin
                      ? new Date(userProfile.lastLogin).toLocaleDateString()
                      : 'Today'}
                  </span>
                </div>
              </div>
            </motion.div>

            <motion.div
              className="profile-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <h2>Professional Information</h2>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Role</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="role"
                      value={editedProfile.role}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your role"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.role || 'Not set'}</span>
                  )}
                </div>
                <div className="info-item">
                  <span className="info-label">Skills</span>
                  {isEditing ? (
                    <input
                      type="text"
                      name="skills"
                      value={editedProfile.skills}
                      onChange={handleChange}
                      className="profile-input"
                      placeholder="Enter your skills (comma separated)"
                    />
                  ) : (
                    <span className="info-value">{userProfile?.skills || 'Not set'}</span>
                  )}
                </div>
              </div>
            </motion.div>
          </div>

          <div className="profile-actions">
            <button className="action-button secondary" onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </button>
            <button className="action-button danger" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Profile

