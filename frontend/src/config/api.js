// API Configuration and Integration
// ===========================================

// Base API URL - Backend running on port 8000
// In Vite, use import.meta.env instead of process.env
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: '/auth/login',
  GOOGLE_LOGIN: '/auth/google-login',
  LOGOUT: '/auth/logout',
  SIGNUP: '/auth/signup',
  ME: '/auth/me',
  FORGOT_PASSWORD_SEND_CODE: '/auth/forgot-password/send-code',
  FORGOT_PASSWORD_VERIFY_CODE: '/auth/forgot-password/verify-code',
  FORGOT_PASSWORD_RESET: '/auth/forgot-password/reset',

  // User Profile
  GET_PROFILE: '/user/profile',
  UPDATE_PROFILE: '/user/profile',

  // Resume Upload
  UPLOAD_USER_PROFILE: '/resumes/upload/user-profile',

  // Admin Endpoints
  ADMIN_STATS: '/admin/stats',
  ADMIN_USERS: '/admin/users',
  ADMIN_UPLOAD_RESUMES: '/resumes/upload',
}

/**
 * Get authentication token from localStorage
 */
export const getAuthToken = () => {
  return localStorage.getItem('authToken')
}

/**
 * Set authentication token in localStorage
 */
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('authToken', token)
  } else {
    localStorage.removeItem('authToken')
  }
}

/**
 * Make an API request with authentication
 * @param {string} endpoint - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise} - API response
 */
export const apiRequest = async (endpoint, options = {}) => {
  const token = getAuthToken()

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    })

    // Check content type before parsing JSON
    const contentType = response.headers.get('content-type')
    let data = {}

    if (contentType && contentType.includes('application/json')) {
      try {
        data = await response.json()
      } catch (jsonError) {
        // If JSON parsing fails, use status text as error message
        console.error('Failed to parse JSON response:', jsonError)
        data = { message: response.statusText || 'Invalid response from server' }
      }
    } else {
      // Non-JSON response, create error data
      const text = await response.text()
      data = { message: text || response.statusText || 'Invalid response from server' }
    }

    if (!response.ok) {
      const errorMessage = data.detail || data.message || `API Error: ${response.statusText}`
      const error = new Error(errorMessage)
      error.status = response.status
      error.data = data
      throw error
    }

    return data
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Could not connect to server. Please check if backend is running.')
    }
    throw error
  }
}

/**
 * Upload file to API
 * @param {string} endpoint - API endpoint
 * @param {FormData} formData - Form data with file
 * @returns {Promise} - API response
 */
export const uploadFile = async (endpoint, formData) => {
  const token = getAuthToken()

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    })

    // Check content type before parsing JSON
    const contentType = response.headers.get('content-type')
    let data = {}

    if (contentType && contentType.includes('application/json')) {
      try {
        data = await response.json()
      } catch (jsonError) {
        // If JSON parsing fails, use status text as error message
        console.error('Failed to parse JSON response:', jsonError)
        data = { message: response.statusText || 'Invalid response from server' }
      }
    } else {
      // Non-JSON response, create error data
      const text = await response.text()
      data = { message: text || response.statusText || 'Invalid response from server' }
    }

    if (!response.ok) {
      const errorMessage = data.detail || data.message || `Upload Error: ${response.statusText}`
      const error = new Error(errorMessage)
      error.status = response.status
      error.data = data
      throw error
    }

    return data
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Could not connect to server. Please check if backend is running.')
    }
    throw error
  }
}

// Authentication API Functions
// =============================

/**
 * Login user
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise} - Login response with token and user data
 */
export const login = async (email, password) => {
  const data = await apiRequest(API_ENDPOINTS.LOGIN, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })

  if (data.access_token) {
    setAuthToken(data.access_token)
  }

  return data
}

export const googleLogin = async (credential) => {
  const data = await apiRequest(API_ENDPOINTS.GOOGLE_LOGIN, {
    method: 'POST',
    body: JSON.stringify({ credential }),
  })

  if (data.access_token) {
    setAuthToken(data.access_token)
  }

  return data
}

/**
 * Register new user
 * @param {object} userData - User registration data
 * @returns {Promise} - Registration response
 */
export const register = async (userData) => {
  return await apiRequest(API_ENDPOINTS.SIGNUP, {
    method: 'POST',
    body: JSON.stringify(userData),
  })
}

/**
 * Get current user info
 * @returns {Promise} - Current user data
 */
export const getCurrentUser = async () => {
  return await apiRequest(API_ENDPOINTS.ME)
}

/**
 * Logout user
 * @returns {Promise} - Logout response
 */
export const logout = async () => {
  try {
    await apiRequest(API_ENDPOINTS.LOGOUT, {
      method: 'POST',
    })
  } catch (error) {
    // Even if logout fails on server, clear local token
    console.error('Logout error:', error)
  } finally {
    setAuthToken(null)
    localStorage.removeItem('userProfile')
    localStorage.removeItem('isAuthenticated')
  }
}

// Forgot Password APIs
// =====================

/**
 * Send password reset verification code to email
 * @param {string} email
 */
export const sendPasswordResetCode = async (email) => {
  return await apiRequest(API_ENDPOINTS.FORGOT_PASSWORD_SEND_CODE, {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

/**
 * Verify password reset code
 * @param {string} email
 * @param {string} code
 */
export const verifyPasswordResetCode = async (email, code) => {
  return await apiRequest(API_ENDPOINTS.FORGOT_PASSWORD_VERIFY_CODE, {
    method: 'POST',
    body: JSON.stringify({ email, code }),
  })
}

/**
 * Reset password with verification code
 * @param {string} email
 * @param {string} code
 * @param {string} newPassword
 */
export const resetPassword = async (email, code, newPassword) => {
  return await apiRequest(API_ENDPOINTS.FORGOT_PASSWORD_RESET, {
    method: 'POST',
    body: JSON.stringify({ email, code, newPassword }),
  })
}

/**
 * Get detailed user profile from backend
 * @returns {Promise} - User profile data
 */
export const getProfile = async () => {
  return await apiRequest(API_ENDPOINTS.GET_PROFILE)
}

/**
 * Update user profile
 * @param {object} profileData - Profile fields to update
 * @returns {Promise} - Updated profile data
 */
export const updateProfile = async (profileData) => {
  return await apiRequest(API_ENDPOINTS.UPDATE_PROFILE, {
    method: 'PUT',
    body: JSON.stringify(profileData),
  })
}

// Resume Upload API Functions
// ============================

/**
 * Upload resume with user profile data
 * @param {File} file - Resume file
 * @param {object} profileData - User profile data (userType, fullName, email, phone)
 * @returns {Promise} - Upload response
 */
export const uploadResumeWithProfile = async (file, profileData = {}) => {
  const formData = new FormData()
  formData.append('file', file)

  if (profileData.userType) {
    formData.append('userType', profileData.userType)
  }
  if (profileData.fullName) {
    formData.append('fullName', profileData.fullName)
  }
  if (profileData.email) {
    formData.append('email', profileData.email)
  }
  if (profileData.phone) {
    formData.append('phone', profileData.phone)
  }

  // Additional fields for richer profile data
  if (profileData.experience) {
    formData.append('experience', profileData.experience)
  }
  if (profileData.skills) {
    formData.append('skills', profileData.skills)
  }
  if (profileData.location) {
    formData.append('location', profileData.location)
  }
  if (profileData.education) {
    formData.append('education', profileData.education)
  }
  if (profileData.role) {
    formData.append('role', profileData.role)
  }
  if (profileData.noticePeriod !== undefined) {
    formData.append('noticePeriod', profileData.noticePeriod)
  }
  if (profileData.readyToRelocate !== undefined) {
    formData.append('readyToRelocate', profileData.readyToRelocate)
  }
  if (profileData.preferredLocation) {
    formData.append('preferredLocation', profileData.preferredLocation)
  }

  return await uploadFile(API_ENDPOINTS.UPLOAD_USER_PROFILE, formData)
}

