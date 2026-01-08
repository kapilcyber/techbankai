import { useState } from 'react'
import { motion } from 'framer-motion'
import { API_BASE_URL } from '../../config/api'
import './SearchUsingJD.css'

const ResultCard = ({ match, index }) => {
  const [showAllSkills, setShowAllSkills] = useState(false);

  // Helper to get initials
  const getInitials = (name) => {
    if (!name || name === 'Unknown Candidate') return '??';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  };

  const skills = match.matched_skills || [];
  const displaySkills = showAllSkills ? skills : skills.slice(0, 5);
  const hasMoreSkills = skills.length > 5;

  return (
    <motion.div
      className="result-card"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
    >
      <div className="match-score-pill">
        <span className={`score-dot ${match.match_score >= 70 ? 'high' : match.match_score >= 40 ? 'medium' : 'low'}`}></span>
        {Math.round(match.match_score)}% Match
      </div>

      <div className="card-top-info">
        <div className="candidate-initials">
          {getInitials(match.candidate_name)}
        </div>
        <div className="candidate-meta">
          <div className="candidate-name-row">
            <h4>{match.candidate_name}</h4>
          </div>
          <div className="meta-badges">
            <span className="user-type-badge">{match.user_type}</span>
            <span className="match-detail-badge" title="Responsibilities">Resp: {Math.round(match.semantic_score || 0)}%</span>
            <span className="match-detail-badge" title="Experience">Exp: {Math.round(match.experience_match || 0)}%</span>
            <span className="match-detail-badge" title="Skills & Certs">Skills: {Math.round(match.skill_match || 0)}%</span>
          </div>
        </div>
      </div>

      <div className="info-blocks-grid">
        <div className="info-block">
          <span className="info-label">Current Role</span>
          <span className="info-value role-text-highlight">{match.role || 'N/A'}</span>
        </div>
        <div className="info-block">
          <span className="info-label">Experience</span>
          <span className="info-value">
            {match.experience_years ? `${match.experience_years} Years` : 'N/A'}
          </span>
        </div>
        <div className="info-block">
          <span className="info-label">Notice Period</span>
          <span className="info-value">
            {match.notice_period !== undefined ? `${match.notice_period} Days` : 'N/A'}
          </span>
        </div>
        <div className="info-block">
          <span className="info-label">Location</span>
          <span className="info-value">
            {match.location || 'N/A'}
            {match.ready_to_relocate && (
              <span className="relocate-subtext" title={`Preferred: ${match.preferred_location}`}>
                ✈️ {match.preferred_location || 'Open'}
              </span>
            )}
          </span>
        </div>
      </div>

      <div className="card-skills-section">
        <span className="skills-title">Matched Skills</span>
        <div className="skills-tag-list">
          {displaySkills.length > 0 ? (
            displaySkills.map((skill, i) => (
              <span key={i} className="skill-result-tag">{skill}</span>
            ))
          ) : (
            <span className="na-text">No matching skills found</span>
          )}
        </div>
        {hasMoreSkills && (
          <button
            className="more-skills-btn"
            onClick={() => setShowAllSkills(!showAllSkills)}
          >
            {showAllSkills ? 'Show Less' : `+${skills.length - 5} more`}
          </button>
        )}
      </div>

      <div className="view-resume-action">
        <a href={match.file_url} target="_blank" rel="noreferrer" className="view-resume-link">
          📄 View Resume
        </a>
      </div>
    </motion.div>
  );
};

const SearchUsingJD = () => {
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  // New state variables for API integration
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)
  const [locationFilter, setLocationFilter] = useState('')
  const [jdMethod, setJdMethod] = useState('upload') // 'upload' or 'manual'
  const [jdText, setJdText] = useState('')

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (selectedFile) => {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(selectedFile.type)) {
      alert('Please upload a PDF or DOCX file')
      return
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      alert('File size should be less than 10MB')
      return
    }

    setFile(selectedFile)
    // Clear previous results when new file is selected
    setResults(null)
    setError(null)
  }

  const handleRemoveFile = () => {
    setFile(null)
    setResults(null)
  }

  const handleFindCandidates = async () => {
    if (jdMethod === 'upload' && !file) {
      alert('Please upload a job description file first')
      return
    }
    if (jdMethod === 'manual' && !jdText.trim()) {
      alert('Please enter or paste a job description first')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const formData = new FormData()
      if (jdMethod === 'upload') {
        formData.append('file', file)
      } else {
        formData.append('jd_text_manual', jdText)
      }

      // Append query parameters
      const params = new URLSearchParams()
      params.append('min_score', '10')
      params.append('top_n', '50')

      const token = localStorage.getItem('authToken')

      const response = await fetch(`${API_BASE_URL}/jd/analyze?${params.toString()}`, {
        method: 'POST',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` })
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = typeof errorData.detail === 'string'
          ? errorData.detail
          : (Array.isArray(errorData.detail)
            ? errorData.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
            : JSON.stringify(errorData.detail) || 'Failed to analyze JD')
        throw new Error(errorMessage)
      }

      const data = await response.json()
      console.log('JD Analysis Results:', data) // Debugging 0% match issues
      setResults(data)

    } catch (err) {
      console.error('JD Analysis error:', err)
      const errorMsg = err instanceof Error ? err.message : (typeof err === 'string' ? err : JSON.stringify(err))
      setError(errorMsg === '{}' ? 'An unexpected error occurred' : errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-using-jd">
      {/* Selection removed here as requested */}

      <motion.div
        className="upload-jd-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <h2>📄 Job Description</h2>
        <p>Provide a job description to find the best matching candidates from your pool.</p>

        <div className="jd-method-tabs">
          <button
            className={`jd-tab ${jdMethod === 'upload' ? 'active' : ''}`}
            onClick={() => setJdMethod('upload')}
          >
            📁 Upload File
          </button>
          <button
            className={`jd-tab ${jdMethod === 'manual' ? 'active' : ''}`}
            onClick={() => setJdMethod('manual')}
          >
            ✍️ Manual Entry
          </button>
        </div>

        {jdMethod === 'upload' ? (
          <div
            className={`jd-drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {!file ? (
              <>
                <div className="upload-icon">📁</div>
                <h3>Upload File</h3>
                <p>Drag and drop your PDF or DOCX here, or click to browse.</p>
                <label htmlFor="jd-file-input" className="browse-jd-btn">
                  Browse Files
                </label>
                <input
                  id="jd-file-input"
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <p className="file-format-hint">Accepted formats: PDF, DOCX (Max size: 10MB)</p>
              </>
            ) : (
              <div className="file-preview-jd">
                <div className="file-icon-jd">📄</div>
                <div className="file-info-jd">
                  <h3>{file.name}</h3>
                  <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <button className="remove-file-btn" onClick={handleRemoveFile}>
                  ✕
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="jd-manual-entry">
            <textarea
              placeholder="Paste the job description text here... (e.g. required skills, years of experience, responsibilities)"
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              className="jd-textarea"
            />
          </div>
        )}

        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}

        <button
          className="find-candidates-btn"
          onClick={handleFindCandidates}
          disabled={loading || (jdMethod === 'upload' ? !file : !jdText.trim())}
        >
          {loading ? 'Analyzing...' : '🚀 Find Matching Candidates'}
        </button>
      </motion.div>

      {/* Results Section */}
      {results && (
        <motion.div
          className="results-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="results-header">
            <h3>Analysis Results</h3>
            <div className="results-summary-badges">
              <span className="summary-badge total">
                Found {results.total_matches} Total
              </span>
              <span className="summary-badge visible">
                Showing {results.top_matches.filter(m => !locationFilter || (m.location && m.location.toLowerCase().includes(locationFilter.toLowerCase())) || (m.preferred_location && m.preferred_location.toLowerCase().includes(locationFilter.toLowerCase()))).length} Visible
              </span>
            </div>
          </div>

          <div className="extracted-requirements">
            <h4>Job Requirements Identified:</h4>
            <div className="jd-skills-tags">
              {results.jd_requirements?.required_skills
                ?.filter(skill => skill.length < 50)
                .map((skill, i) => (
                  <span key={i} className="jd-skill-tag required">{skill}</span>
                ))}
              {results.jd_requirements?.preferred_skills
                ?.filter(skill => skill.length < 50)
                .map((skill, i) => (
                  <span key={i} className="jd-skill-tag preferred">{skill}</span>
                ))}
            </div>
          </div>

          <div className="results-container-main">
            <aside className="results-sidebar">


              <div className="filter-group">
                <h4>Preferred Location</h4>
                <div className="sidebar-search-box">
                  <input
                    type="text"
                    placeholder="Search location..."
                    value={locationFilter}
                    onChange={(e) => setLocationFilter(e.target.value)}
                  />
                  <span className="search-icon-sm">🔍</span>
                </div>
              </div>
            </aside>

            <div className="results-list-wrapper">
              <div className="results-list">
                {results.top_matches
                  .filter(m => !locationFilter || (m.location && m.location.toLowerCase().includes(locationFilter.toLowerCase())) || (m.preferred_location && m.preferred_location.toLowerCase().includes(locationFilter.toLowerCase())))
                  .length === 0 ? (
                  <p className="no-matches">No candidates match the selected filters.</p>
                ) : (
                  results.top_matches
                    .filter(m => !locationFilter || (m.location && m.location.toLowerCase().includes(locationFilter.toLowerCase())) || (m.preferred_location && m.preferred_location.toLowerCase().includes(locationFilter.toLowerCase())))
                    .map((match, index) => (
                      <ResultCard key={match.resume_id} match={match} index={index} />
                    ))
                )}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default SearchUsingJD


