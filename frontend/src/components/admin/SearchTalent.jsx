import { useState } from 'react'
import { motion } from 'framer-motion'
import { API_BASE_URL } from '../../config/api'
import './SearchTalent.css'

const SearchTalent = () => {
  const [filters, setFilters] = useState({
    userType: '',
    minExperience: '',
    location: '',
    phone: '',
    email: '',
    department: '',
    role: '',
    skills: ''
  })
  const [searchResults, setSearchResults] = useState([])
  const [hasSearched, setHasSearched] = useState(false)
  const [loading, setLoading] = useState(false)

  const userTypes = ['Company Employee', 'Freelancer', 'Guest User']

  const roleOptions = ['Data Analytics', 'Data Engineer', 'Cloud Operator', 'DevOps', 'SDE', 'Network Engineer']
  const departmentOptions = ['Data & AI', 'Cloud', 'Cyber Security', 'Infra']
  const skillOptions = ['Python', 'Java', 'C++', 'C', 'JS', 'PowerBI', 'AI/ML', 'Excel', 'SQL', 'AWS']
  const locationOptions = ['Gurgaon', 'Delhi', 'Noida', 'Pune', 'Hyderabad', 'Mumbai', 'Bangalore']

  const handleInputChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSearch = async () => {
    try {
      setLoading(true)
      setHasSearched(true)

      // Build query parameters
      const params = new URLSearchParams()

      if (filters.skills) params.append('skills', filters.skills)
      if (filters.userType) params.append('user_types', filters.userType)
      if (filters.minExperience) params.append('min_experience', filters.minExperience)
      if (filters.location) params.append('locations', filters.location)
      if (filters.role) params.append('roles', filters.role)
      if (filters.email) params.append('q', filters.email)

      const token = localStorage.getItem('authToken')

      const response = await fetch(`${API_BASE_URL}/resumes/search?${params.toString()}`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` })
        }
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data = await response.json()
      setSearchResults(data.resumes || data || [])
    } catch (error) {
      console.error('Search error:', error)
      setSearchResults([])
      alert('Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setFilters({
      userType: '',
      minExperience: '',
      location: '',
      phone: '',
      email: '',
      department: '',
      role: '',
      skills: ''
    })
    setSearchResults([])
    setHasSearched(false)
  }

  const getInitials = (name) => {
    if (!name || name === 'Unknown') return '??'
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className="search-talent">
      <motion.div
        className="search-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h2>Search Talent</h2>
        <p>Find ideal candidates using advanced filtering and AI-powered matching.</p>
      </motion.div>

      <motion.div
        className="search-filters-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <h3>🔍 Filter Candidates</h3>

        <div className="filters-grid">
          <div className="filter-group">
            <label>User Type</label>
            <select
              value={filters.userType}
              onChange={(e) => handleInputChange('userType', e.target.value)}
            >
              <option value="">All User Types</option>
              {userTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Min Experience (Years)</label>
            <input
              type="number"
              value={filters.minExperience}
              onChange={(e) => handleInputChange('minExperience', e.target.value)}
              placeholder="e.g. 2"
              min="0"
            />
          </div>

          <div className="filter-group">
            <label>Location</label>
            <div className="hybrid-input-wrapper">
              <input
                type="text"
                list="location-list"
                value={filters.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                placeholder="City or Region"
                className="hybrid-input"
              />
              <datalist id="location-list">
                {locationOptions.map((location) => (
                  <option key={location} value={location} />
                ))}
              </datalist>
            </div>
          </div>

          <div className="filter-group">
            <label>Email / Phone</label>
            <input
              type="text"
              value={filters.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="Search by contact info"
            />
          </div>

          <div className="filter-group">
            <label>Role</label>
            <div className="hybrid-input-wrapper">
              <input
                type="text"
                list="role-list"
                value={filters.role}
                onChange={(e) => handleInputChange('role', e.target.value)}
                placeholder="Job Role"
                className="hybrid-input"
              />
              <datalist id="role-list">
                {roleOptions.map((role) => (
                  <option key={role} value={role} />
                ))}
              </datalist>
            </div>
          </div>

          <div className="filter-group">
            <label>Technical Skills</label>
            <div className="hybrid-input-wrapper">
              <input
                type="text"
                list="skills-list"
                value={filters.skills}
                onChange={(e) => handleInputChange('skills', e.target.value)}
                placeholder="e.g. Python, React (comma separated)"
                className="hybrid-input"
              />
              <datalist id="skills-list">
                {skillOptions.map((skill) => (
                  <option key={skill} value={skill} />
                ))}
              </datalist>
            </div>
          </div>
        </div>

        <div className="filter-actions">
          <button className="search-btn" onClick={handleSearch} disabled={loading}>
            {loading ? 'Searching...' : '🔍 Search Candidates'}
          </button>
          <button className="clear-btn" onClick={handleClear} disabled={loading}>
            Clear Filters
          </button>
        </div>
      </motion.div>

      <motion.div
        className="search-results-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <div className="results-header">
          <h3>Search Results</h3>
          <span className="results-count">
            {searchResults.length} {searchResults.length === 1 ? 'Candidate' : 'Candidates'} Found
          </span>
        </div>

        <div className="results-content">
          {!hasSearched ? (
            <p className="empty-message">Enter filters above and click Search to find talent.</p>
          ) : searchResults.length === 0 ? (
            <p className="empty-message">No candidates found matching your criteria.</p>
          ) : (
            <div className="results-list">
              {searchResults.map((result, index) => {
                const name = result.name || result.full_name || 'Unknown Candidate';
                const initials = getInitials(name);
                const matchedSkills = result.matched_skills || [];
                const allSkills = result.skills || [];

                return (
                  <motion.div
                    key={result.id || result.resume_id || index}
                    className="talent-premium-card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <div className="talent-card-header">
                      <div className="talent-profile-main">
                        <div className="talent-avatar">{initials}</div>
                        <div className="talent-title-area">
                          <h4>{name}</h4>
                          <div className="talent-badges">
                            <span className={`talent-type-badge ${String(result.user_type || result.source_type || 'candidate').toLowerCase().replace(/\s+/g, '_')}`}>
                              {result.user_type || result.source_type || 'Candidate'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="talent-card-body">
                      {/* Professional Metric Grid */}
                      <div className="talent-metrics-grid">
                        <div className="talent-metric">
                          <label>Experience</label>
                          <p>{result.experience_years ? `${result.experience_years} Years` : 'N/A'}</p>
                        </div>
                        <div className="talent-metric">
                          <label>Notice</label>
                          <p>{result.notice_period !== undefined ? `${result.notice_period} Days` : 'N/A'}</p>
                        </div>
                        <div className="talent-metric full-span">
                          <label>Current Role</label>
                          <p className="role-text-highlight">{result.role || 'Not Mentioned'}</p>
                        </div>
                        <div className="talent-metric full-span">
                          <label>Location</label>
                          <p>{result.location || 'N/A'}</p>
                        </div>
                      </div>

                      {allSkills.length > 0 && (
                        <div className="talent-skills-section">
                          <label>Featured Skills</label>
                          <div className="talent-skills-list">
                            {allSkills.slice(0, 4).map((skill, idx) => (
                              <span
                                key={idx}
                                className={`talent-skill-badge ${matchedSkills.includes(skill) ? 'matched' : ''}`}
                              >
                                {skill}
                              </span>
                            ))}
                            {allSkills.length > 4 && (
                              <span className="talent-more-count">+{allSkills.length - 4}</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="talent-card-footer">
                      <div className="match-status">
                        {filters.skills && (
                          <div className="match-pill">
                            <span className="match-value">
                              {Math.round((matchedSkills.length / filters.skills.split(',').filter(s => s.trim()).length) * 100)}% Match
                            </span>
                          </div>
                        )}
                      </div>
                      <a href={result.file_url} target="_blank" rel="noreferrer" className="talent-action-btn">
                        <span>📄</span> Resume
                      </a>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}

export default SearchTalent


