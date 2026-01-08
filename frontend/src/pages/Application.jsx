import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { uploadResumeWithProfile } from '../config/api'
import Navbar from '../components/Navbar'
import './Application.css'

const Application = () => {
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    country: '',
    zipCode: '',
    experience: '',
    skills: '',
    role: '',
    education: '',
    linkedIn: '',
    portfolio: '',
    currentlyWorking: true,
    currentCompany: '',
    readyToRelocate: false,
    preferredLocation: '',
    noticePeriod: 0
  })
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const { selectedEmploymentType, userProfile } = useApp()

  // File upload handlers
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

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    } else {
      // Form field change
      setFormData({
        ...formData,
        [e.target.name]: e.target.value
      })
    }
  }

  const handleFile = (selectedFile) => {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(selectedFile.type)) {
      alert('Please upload a PDF or DOCX document')
      return
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      alert('File size should be less than 5MB')
      return
    }

    setFile(selectedFile)
  }

  const handleRemove = () => {
    setFile(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!file) {
      alert('Please upload your CV/Resume first')
      return
    }

    setSubmitting(true)

    try {
      // Prepare profile data for upload
      // Prepare profile data for upload
      const profileData = {
        userType: selectedEmploymentType?.title || selectedEmploymentType?.name || 'Guest User',
        fullName: `${formData.firstName} ${formData.lastName}`.trim(),
        email: formData.email || userProfile?.email || '',
        phone: formData.phone || '',
        address: formData.address || '',
        city: formData.city || '',
        country: formData.country || '',
        experience: formData.experience || '0',
        skills: formData.skills || '',
        role: formData.role || '',
        location: [formData.city, formData.country].filter(Boolean).join(', '),
        education: formData.education || '',
        noticePeriod: parseInt(formData.noticePeriod) || 0,
        currentlyWorking: formData.currentlyWorking,
        currentCompany: formData.currentCompany,
        readyToRelocate: formData.readyToRelocate,
        preferredLocation: formData.preferredLocation
      }

      // Upload resume with profile data
      const result = await uploadResumeWithProfile(file, profileData)

      setSubmitting(false)
      alert(`Application submitted successfully! Resume ID: ${result.resume_id}`)
      navigate('/dashboard')
    } catch (error) {
      console.error('Application submission error:', error)
      alert(error.message || 'Failed to submit application. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="application-container">
      <div className="animated-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
        <div className="gradient-orb orb-4"></div>
      </div>

      <Navbar userProfile={userProfile} />

      <div className="application-content">
        <motion.div
          className="application-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="header-glass"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h1>Submit Your Application</h1>
            <p>Upload your CV/Resume and fill in your personal information</p>
            {selectedEmploymentType && (
              <motion.div
                className="employment-type-badge"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.4 }}
              >
                {selectedEmploymentType.title}
              </motion.div>
            )}
          </motion.div>
        </motion.div>

        <motion.form
          className="application-form"
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          {/* CV Upload Section */}
          <motion.div
            className="form-section upload-section"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <h2>Upload CV/Resume</h2>
            <div
              className={`drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {!file ? (
                <>
                  <motion.div
                    className="upload-icon"
                    animate={{ y: [0, -10, 0] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    📄
                  </motion.div>
                  <h3>Drag & Drop your CV/Resume here</h3>
                  <p>or</p>
                  <label htmlFor="file-input" className="browse-button">
                    Browse Files
                  </label>
                  <input
                    id="file-input"
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleChange}
                    style={{ display: 'none' }}
                  />
                  <p className="file-hint">Supported formats: PDF, DOCX (Max 5MB)</p>
                </>
              ) : (
                <motion.div
                  className="file-preview"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <div className="file-icon">📄</div>
                  <div className="file-info">
                    <h3>{file.name}</h3>
                    <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <button type="button" className="remove-button" onClick={handleRemove}>
                    ✕
                  </button>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Personal Information Section */}
          <motion.div
            className="form-section"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <h2>Personal Information</h2>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="firstName">First Name *</label>
                <input
                  type="text"
                  id="firstName"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="lastName">Last Name *</label>
                <input
                  type="text"
                  id="lastName"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="phone">Phone *</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </motion.div>

          <motion.div
            className="form-section"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <h2>Address</h2>
            <div className="form-group">
              <label htmlFor="address">Street Address</label>
              <input
                type="text"
                id="address"
                name="address"
                value={formData.address}
                onChange={handleChange}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="city">City</label>
                <input
                  type="text"
                  id="city"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                />
              </div>
              <div className="form-group">
                <label htmlFor="country">Country</label>
                <input
                  type="text"
                  id="country"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                />
              </div>
              <div className="form-group">
                <label htmlFor="zipCode">Zip Code</label>
                <input
                  type="text"
                  id="zipCode"
                  name="zipCode"
                  value={formData.zipCode}
                  onChange={handleChange}
                />
              </div>
            </div>
          </motion.div>

          <motion.div
            className="form-section"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
          >
            <h2>Professional Information</h2>
            <div className="form-group">
              <label htmlFor="experience">Years of Experience</label>
              <input
                type="number"
                id="experience"
                name="experience"
                value={formData.experience}
                onChange={handleChange}
                min="0"
              />
            </div>
            <div className="form-group">
              <label htmlFor="role">Professional Role *</label>
              <input
                type="text"
                id="role"
                name="role"
                value={formData.role}
                onChange={handleChange}
                placeholder="e.g., Software Engineer, Data Scientist"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="skills">Skills (comma separated)</label>
              <input
                type="text"
                id="skills"
                name="skills"
                value={formData.skills}
                onChange={handleChange}
                placeholder="e.g., React, Node.js, Python"
              />
            </div>
            {true && (
              <>
                {/* Currently Working Toggle */}
                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label style={{ fontWeight: '600', marginBottom: '8px', display: 'block' }}>Currently Working?</label>
                  <div className="relocation-toggle-group" style={{ display: 'flex', gap: '12px' }}>
                    <button
                      type="button"
                      className={`toggle-option ${formData.currentlyWorking ? 'active' : ''}`}
                      onClick={() => setFormData(prev => ({ ...prev, currentlyWorking: true }))}
                      style={{
                        flex: 1,
                        padding: '12px',
                        borderRadius: '12px',
                        border: '2px solid #3282b8',
                        background: formData.currentlyWorking ? '#3282b8' : 'rgba(255, 255, 255, 0.5)',
                        color: formData.currentlyWorking ? 'white' : '#3282b8',
                        fontWeight: '700',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        boxShadow: formData.currentlyWorking ? '0 4px 12px rgba(50, 130, 184, 0.3)' : 'none'
                      }}
                    >
                      Yes
                    </button>
                    <button
                      type="button"
                      className={`toggle-option ${!formData.currentlyWorking ? 'active' : ''}`}
                      onClick={() => setFormData(prev => ({ ...prev, currentlyWorking: false }))}
                      style={{
                        flex: 1,
                        padding: '12px',
                        borderRadius: '12px',
                        border: '2px solid #3282b8',
                        background: !formData.currentlyWorking ? '#3282b8' : 'rgba(255, 255, 255, 0.5)',
                        color: !formData.currentlyWorking ? 'white' : '#3282b8',
                        fontWeight: '700',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        boxShadow: !formData.currentlyWorking ? '0 4px 12px rgba(50, 130, 184, 0.3)' : 'none'
                      }}
                    >
                      No
                    </button>
                  </div>
                </div>

                {/* Current Company Name (conditional) */}
                {formData.currentlyWorking && (
                  <motion.div
                    className="form-group"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ marginBottom: '1.5rem' }}
                  >
                    <label htmlFor="currentCompany">Current Company Name</label>
                    <input
                      type="text"
                      id="currentCompany"
                      name="currentCompany"
                      value={formData.currentCompany}
                      onChange={handleChange}
                      placeholder="e.g., Google, Microsoft, Accenture"
                      autoComplete="off"
                    />
                  </motion.div>
                )}

                {/* Ready to Relocate Toggle */}
                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label style={{ fontWeight: '600', marginBottom: '8px', display: 'block' }}>Ready to Relocate?</label>
                  <div className="relocation-toggle-group" style={{ display: 'flex', gap: '12px' }}>
                    <button
                      type="button"
                      className={`toggle-option ${formData.readyToRelocate ? 'active' : ''}`}
                      onClick={() => setFormData(prev => ({ ...prev, readyToRelocate: true }))}
                      style={{
                        flex: 1,
                        padding: '12px',
                        borderRadius: '12px',
                        border: '2px solid #3282b8',
                        background: formData.readyToRelocate ? '#3282b8' : 'rgba(255, 255, 255, 0.5)',
                        color: formData.readyToRelocate ? 'white' : '#3282b8',
                        fontWeight: '700',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        boxShadow: formData.readyToRelocate ? '0 4px 12px rgba(50, 130, 184, 0.3)' : 'none'
                      }}
                    >
                      Yes
                    </button>
                    <button
                      type="button"
                      className={`toggle-option ${!formData.readyToRelocate ? 'active' : ''}`}
                      onClick={() => setFormData(prev => ({ ...prev, readyToRelocate: false, preferredLocation: '' }))}
                      style={{
                        flex: 1,
                        padding: '12px',
                        borderRadius: '12px',
                        border: '2px solid #3282b8',
                        background: !formData.readyToRelocate ? '#3282b8' : 'rgba(255, 255, 255, 0.5)',
                        color: !formData.readyToRelocate ? 'white' : '#3282b8',
                        fontWeight: '700',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        boxShadow: !formData.readyToRelocate ? '0 4px 12px rgba(50, 130, 184, 0.3)' : 'none'
                      }}
                    >
                      No
                    </button>
                  </div>
                </div>

                {formData.readyToRelocate && (
                  <motion.div
                    className="form-group"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ marginBottom: '1.5rem' }}
                  >
                    <label htmlFor="preferredLocation">Preferred Relocation Location</label>
                    <input
                      type="text"
                      id="preferredLocation"
                      name="preferredLocation"
                      value={formData.preferredLocation}
                      onChange={handleChange}
                      placeholder="e.g. Mumbai, Remote, Overseas"
                      autoComplete="off"
                    />
                  </motion.div>
                )}

                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label htmlFor="noticePeriod">Notice Period (Days)</label>
                  <input
                    type="number"
                    id="noticePeriod"
                    name="noticePeriod"
                    value={formData.noticePeriod}
                    onChange={handleChange}
                    placeholder="e.g., 30"
                    min="0"
                  />
                </div>
              </>
            )}
            {selectedEmploymentType?.id !== 'guest-user' && (
              <div className="form-group">
                <label htmlFor="education">Education</label>
                <textarea
                  id="education"
                  name="education"
                  value={formData.education}
                  onChange={handleChange}
                  rows="3"
                  placeholder="Enter your educational background"
                />
              </div>
            )}
          </motion.div>

          {selectedEmploymentType?.id !== 'guest-user' && (
            <motion.div
              className="form-section"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.8 }}
            >
              <h2>Links</h2>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="linkedIn">LinkedIn Profile</label>
                  <input
                    type="url"
                    id="linkedIn"
                    name="linkedIn"
                    value={formData.linkedIn}
                    onChange={handleChange}
                    placeholder="https://linkedin.com/in/yourprofile"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="portfolio">Portfolio/Website</label>
                  <input
                    type="url"
                    id="portfolio"
                    name="portfolio"
                    value={formData.portfolio}
                    onChange={handleChange}
                    placeholder="https://yourportfolio.com"
                  />
                </div>
              </div>
            </motion.div>
          )}

          <motion.div
            className="form-actions"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.9 }}
          >
            <button
              type="button"
              className="back-button"
              onClick={() => navigate('/dashboard')}
            >
              ← Back
            </button>
            <button
              type="submit"
              className="submit-button"
              disabled={submitting || !file}
            >
              {submitting ? 'Submitting...' : 'Submit Application'}
            </button>
          </motion.div>
        </motion.form>
      </div>
    </div>
  )
}

export default Application

