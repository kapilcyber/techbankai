import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts'
import { API_BASE_URL } from '../../config/api'
import './AdminDashboard.css'

// Helper to clean text from unwanted characters
const cleanCertText = (text) => {
  if (typeof text !== 'string') return ''
  return text
    .replace(/^[●☐☑✓✔✅❌□■▪▫•◦‣⁃∙⦿⦾]+\s*/g, '')
    .replace(/^[\-\*\d\.]+\s*/g, '')
    .replace(/^[\s\W]+/, '')
    .trim()
}

const getInitials = (name) => {
  if (!name || name === 'N/A') return '??'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
}

const formatUserType = (type) => {
  if (!type || typeof type !== 'string') return 'N/A'
  return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

const renderSafe = (value, fallback = 'N/A') => {
  if (!value) return fallback
  if (typeof value === 'object') {
    return value.email || value.name || value.full_name || JSON.stringify(value)
  }
  return value
}

const AdminDashboard = () => {
  const [selectedUserType, setSelectedUserType] = useState('all')
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [timeframe, setTimeframe] = useState('month') // 'day', 'month', 'quarter'

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('authToken')

      const response = await fetch(`${API_BASE_URL}/admin/stats`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` })
        }
      })

      if (response.status === 401) {
        throw new Error('Unauthorized. Please log in as an admin.')
      }

      if (response.status === 403) {
        throw new Error('Access Denied. Your account permissions have changed. Please LOGOUT and LOGIN again to refresh your access.')
      }

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data')
      }

      const data = await response.json()

      // Transform backend data to match frontend format
      const transformedData = {
        totalRecords: data.total_records ?? data.total_resumes ?? 0,
        totalUsers: data.total_users || 0,
        totalJD: data.total_jd_analyses || 0,
        totalMatches: data.total_matches || 0,
        userTypeCounts: data.user_type_breakdown || {},
        topSkills: data.top_skills || [],
        topSkillsByUserType: data.top_skills_by_user_type || {},
        departments: data.departments || Object.keys(data.user_type_breakdown || {}),
        departmentDistribution: data.departmentDistribution || data.user_type_breakdown || {},
        trends: data.trends || { day: [], month: [], quarter: [] },
        recentResumes: data.recentResumes || data.recent_resumes || [],
        recentJD: data.recent_jd_analyses || []
      }

      setDashboardData(transformedData)
      setError(null)
    } catch (err) {
      console.error('Error fetching dashboard data:', err)
      setError(err.message || 'Failed to load dashboard data. Please check if you are logged in as admin.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading-message">
          <div className="spinner"></div>
          Loading dashboard data...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="admin-dashboard">
        <div className="error-message">
          <h3>Connection Error</h3>
          <p>{error}</p>
          <button onClick={fetchDashboardData} className="retry-btn">
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="admin-dashboard">
        <div className="error-message">No data available</div>
      </div>
    )
  }

  // Calculate filtered data based on selected user type
  const filteredTotal = selectedUserType === 'all'
    ? dashboardData.totalRecords
    : dashboardData.userTypeCounts[selectedUserType] || 0

  const filteredTopSkills = selectedUserType === 'all'
    ? dashboardData.topSkills
    : (dashboardData.topSkillsByUserType?.[selectedUserType] || [])



  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h2>Dashboard Overview</h2>
        <div className="user-type-filter">
          <label>Filter by User Type:</label>
          <select
            value={selectedUserType}
            onChange={(e) => setSelectedUserType(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Types</option>
            <option value="Company Employee">Company Employee</option>
            <option value="Freelancer">Freelancer</option>

            <option value="Guest User">Guest User</option>
          </select>
        </div>
      </div>

      <div className="stats-grid">
        <motion.div
          className="stat-card premium"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="stat-icon-wrapper blue">
            <span>📈</span>
          </div>
          <div className="stat-content">
            <label>Total Talent Pool</label>
            <p className="stat-value">{filteredTotal.toLocaleString()}</p>
            <span className="stat-trend">Global Database</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card premium"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="stat-icon-wrapper green">
            <span>🏢</span>
          </div>
          <div className="stat-content">
            <label>Active Departments</label>
            <p className="stat-value">{dashboardData.departments.length}</p>
            <span className="stat-trend">Cross-Functional</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card premium"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <div className="stat-icon-wrapper purple">
            <span>✅</span>
          </div>
          <div className="stat-content">
            <label>Current Filter</label>
            <p className="stat-value">{filteredTotal}</p>
            <span className="stat-trend">Matched Candidates</span>
          </div>
        </motion.div>
      </div>

      <div className="dashboard-grid">
        <motion.div
          className="dashboard-section trends-analysis"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="section-header-row">
            <h3>Onboarding Trends</h3>
            <div className="timeframe-toggles">
              <button
                className={`toggle-btn ${timeframe === 'day' ? 'active' : ''}`}
                onClick={() => setTimeframe('day')}
              >Day</button>
              <button
                className={`toggle-btn ${timeframe === 'month' ? 'active' : ''}`}
                onClick={() => setTimeframe('month')}
              >Month</button>
              <button
                className={`toggle-btn ${timeframe === 'quarter' ? 'active' : ''}`}
                onClick={() => setTimeframe('quarter')}
              >Quarter</button>
            </div>
          </div>

          <div className="chart-container" style={{ height: '320px', marginTop: '1.5rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dashboardData.trends[timeframe]} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorEmployee" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorFreelancer" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorGuest" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#94a3b8"
                  fontSize={11}
                  fontWeight={600}
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                  tickFormatter={(val) => {
                    if (timeframe === 'day') return val.split('-').slice(1).join('/')
                    return val
                  }}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  fontWeight={600}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                    padding: '12px'
                  }}
                  itemStyle={{ fontSize: '12px', fontWeight: '700' }}
                  labelStyle={{ color: '#0f172a', fontWeight: '800', marginBottom: '8px' }}
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  iconType="circle"
                  wrapperStyle={{ paddingBottom: '20px', fontSize: '12px', fontWeight: '700' }}
                />
                <Area
                  type="monotone"
                  dataKey="Company Employee"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorEmployee)"
                  stackId="1"
                />
                <Area
                  type="monotone"
                  dataKey="Freelancer"
                  stroke="#10b981"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorFreelancer)"
                  stackId="1"
                />
                <Area
                  type="monotone"
                  dataKey="Guest User"
                  stroke="#6366f1"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorGuest)"
                  stackId="1"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div
          className="dashboard-section premium-skills"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="section-header-row">
            <h3>Top Candidate Skills</h3>
            <span className="section-subtitle">Real-time Analytics</span>
          </div>

          <div className="skills-analytics-list">
            {filteredTopSkills.length === 0 ? (
              <div className="no-data-placeholder">
                <p>No skill data detected in database</p>
              </div>
            ) : (
              filteredTopSkills.slice(0, 7).map((item, index) => {
                const percentage = ((item.count / dashboardData.totalRecords) * 100).toFixed(1)
                return (
                  <div key={item.skill} className="skill-analytics-item">
                    <div className="skill-meta">
                      <div className="skill-rank-badge">#{index + 1}</div>
                      <span className="skill-name-text">{item.skill}</span>
                      <span className="skill-count-badge">{item.count} Candidates</span>
                    </div>
                    <div className="skill-progress-track">
                      <motion.div
                        className="skill-progress-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.max(percentage, 5)}%` }}
                        transition={{ duration: 1.2, ease: "easeOut", delay: index * 0.1 }}
                      />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </motion.div>
      </div>

      <motion.div
        className="dashboard-section current-table-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <h3>Current Table</h3>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Candidate Details</th>
                <th>Type</th>
                <th>Role</th>
                <th>Location</th>
                <th>Experience</th>
                <th>Notice</th>
                <th>Relocate</th>
                <th>Skills</th>
                <th>Certifications</th>
              </tr>
            </thead>
            <tbody>
              {dashboardData.recentResumes && dashboardData.recentResumes.length > 0 ? (
                dashboardData.recentResumes.map((resume, index) => (
                  <tr
                    key={resume.id || resume.resume_id}
                    className="clickable-row"
                    onClick={() => setSelectedCandidate(resume)}
                  >
                    <td><span className="id-badge">#{index + 1}</span></td>
                    <td>
                      <div className="name-cell">
                        <div className="avatar-sm">{getInitials(resume.name || resume.full_name || 'N/A')}</div>
                        <div className="name-info">
                          <span className="candidate-name">{renderSafe(resume.name || resume.full_name, 'Anonymous')}</span>
                          <span className="candidate-email-sub">{renderSafe(resume.email, 'No Email')}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`type-badge-new ${resume.user_type || resume.source_type || 'default'}`}>
                        {formatUserType(resume.user_type || resume.source_type)}
                      </span>
                    </td>
                    <td><span className="role-text">{renderSafe(resume.role)}</span></td>
                    <td><span className="location-text">{renderSafe(resume.location)}</span></td>
                    <td>
                      <span className="exp-badge-new">
                        {resume.experience_years ? `${parseFloat(resume.experience_years).toFixed(1)} yrs` : '0 yrs'}
                      </span>
                    </td>
                    <td><span className="notice-text">{resume.notice_period !== undefined ? `${resume.notice_period}d` : 'N/A'}</span></td>
                    <td>
                      <span className={`relocate-pill ${resume.ready_to_relocate ? 'yes' : 'no'}`}>
                        {resume.ready_to_relocate ? 'YES' : 'NO'}
                      </span>
                    </td>
                    <td>
                      <div className="skills-tags-new">
                        {(resume.skills || []).slice(0, 2).map((skill, idx) => (
                          <span key={idx} className="skill-tag-new">{skill}</span>
                        ))}
                        {resume.skills && resume.skills.length > 2 && (
                          <span className="more-count">+{resume.skills.length - 2}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="skills-tags-new">
                        {(resume.parsed_data?.resume_certificates || [])
                          .filter(c => c && c !== "Not mentioned")
                          .slice(0, 1).map((cert, idx) => (
                            <span key={idx} className="cert-tag-new">{cleanCertText(cert)}</span>
                          ))}
                        {resume.parsed_data?.resume_certificates?.filter(c => c && c !== "Not mentioned")?.length > 1 && (
                          <span className="more-count">+{resume.parsed_data.resume_certificates.filter(c => c && c !== "Not mentioned").length - 1}</span>
                        )}
                        {(!(resume.parsed_data?.resume_certificates?.filter(c => c && c !== "Not mentioned")?.length > 0)) && (
                          <span className="na-text">N/A</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '20px' }}>
                    No resumes found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
      <CandidateDetailModal
        candidate={selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
      />
    </div>
  )
}

const CandidateDetailModal = ({ candidate, onClose }) => {
  useEffect(() => {
    if (candidate) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [candidate])

  if (!candidate) return null

  // Helper function to clean text from unwanted characters
  const cleanText = (text) => {
    if (typeof text !== 'string') return ''
    return text
      .replace(/^[●☐☑✓✔✅❌□■▪▫•◦‣⁃∙⦿⦾]+\s*/g, '') // Added ● explicitly
      .replace(/^[\-\*\d\.]+\s*/g, '') // Remove list markers
      .replace(/^[\s\W]+/, '') // Remove any leading non-word characters
      .trim()
  }

  const parsed = candidate.parsed_data || {}
  const workHistory = candidate.work_history || []

  // Use structured certificates if available, otherwise fallback to parsed_data array
  let certs = candidate.certificates || []
  if (certs.length === 0 && parsed.resume_certificates && Array.isArray(parsed.resume_certificates)) {
    certs = parsed.resume_certificates
      .filter(c => c && c !== "Not mentioned")
      .map(name => ({ name: name, issuer: 'Detected', date_obtained: null }))
  }

  const skills = candidate.skills && candidate.skills.length > 0 ? candidate.skills : (parsed.resume_skills || [])
  const projects = parsed.resume_projects || []
  const achievements = parsed.resume_achievements || []

  return createPortal(
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="modal-content"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        onClick={e => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="header-top">
            <div className="candidate-profile-summary">
              <div className="profile-avatar-lg">{getInitials(candidate.name || candidate.full_name || 'N/A')}</div>
              <div className="profile-info-main">
                <h2>{candidate.name || candidate.full_name || 'Candidate Profile'}</h2>
                <div className="header-badges-row">
                  <span className="premium-badge type">{formatUserType(candidate.user_type || candidate.source_type || 'Candidate')}</span>
                  {candidate.role && <span className="premium-badge role">{candidate.role}</span>}
                </div>
              </div>
            </div>
            <button className="close-btn-new" aria-label="Close" onClick={onClose}>&times;</button>
          </div>
        </div>

        <div className="modal-body">
          <div className="modal-grid-container">
            {/* Quick Info Section */}
            <div className="info-cards-row">
              <div className="info-mini-card">
                <span className="mini-icon">📧</span>
                <div className="mini-content">
                  <label>Email Address</label>
                  <p>{renderSafe(candidate.email)}</p>
                </div>
              </div>
              <div className="info-mini-card">
                <span className="mini-icon">📍</span>
                <div className="mini-content">
                  <label>Current Location</label>
                  <p>{renderSafe(candidate.location)}</p>
                </div>
              </div>
              <div className="info-mini-card">
                <span className="mini-icon">💼</span>
                <div className="mini-content">
                  <label>Total Experience</label>
                  <p>{candidate.experience_years ? `${parseFloat(candidate.experience_years).toFixed(1)} Years` : 'N/A'}</p>
                </div>
              </div>
              <div className="info-mini-card">
                <span className="mini-icon">⏳</span>
                <div className="mini-content">
                  <label>Notice Period</label>
                  <p>{candidate.notice_period !== undefined ? `${candidate.notice_period} Days` : 'N/A'}</p>
                </div>
              </div>
            </div>

            <div className="details-secondary-row">
              <div className="detail-item-premium full-width">
                <label>Relocation Status</label>
                <div className={`status-box ${candidate.ready_to_relocate ? 'active' : ''}`}>
                  {candidate.ready_to_relocate ? `Ready to Relocate (Preferred: ${candidate.preferred_location || 'Open'})` : 'Not open to relocation'}
                </div>
              </div>
            </div>

            <div className="skills-certs-grid">
              <div className="content-block">
                <h3><span className="block-icon">🚀</span> Core Skills</h3>
                <div className="premium-tag-list">
                  {skills.length > 0 ? (
                    skills.map((skill, idx) => (
                      <span key={idx} className="premium-skill-tag">{skill}</span>
                    ))
                  ) : <p className="no-data-text">No skills detected</p>}
                </div>
              </div>

              <div className="content-block">
                <h3><span className="block-icon">📜</span> Certifications</h3>
                <div className="premium-tag-list">
                  {certs.length > 0 ? (
                    certs.map((cert, idx) => (
                      <span key={idx} className="premium-cert-tag">{cleanCertText(cert.name)}</span>
                    ))
                  ) : <p className="no-data-text">No certifications found</p>}
                </div>
              </div>
            </div>
          </div>
        </div>

        {candidate.file_url && (
          <div className="modal-footer-premium">
            <a
              href={candidate.file_url}
              target="_blank"
              rel="noreferrer"
              className="view-resume-action-btn"
            >
              📄 View Full Resume
            </a>
          </div>
        )}
      </motion.div>
    </motion.div>,
    document.body
  )
}

const getDepartmentColor = (dept) => {
  const colors = {
    'Company Employee': '#3282b8',
    'Freelancer': '#00d4ff',

    'Guest User': '#0f4c75',
    'Engineering': '#3282b8',
    'Design': '#00d4ff',
    'Marketing': '#bbe1fa',
    'Sales': '#0f4c75',
    'HR': '#43e97b'
  }
  return colors[dept] || '#3282b8'
}

export default AdminDashboard

