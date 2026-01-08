import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { uploadResumeWithProfile } from '../config/api'
import Navbar from '../components/Navbar'
import './CVUpload.css'

const CVUpload = () => {
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const navigate = useNavigate()
  const { selectedEmploymentType, userProfile } = useApp()

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
    }
  }

  const handleFile = (selectedFile) => {
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(selectedFile.type)) {
      alert('Please upload a PDF or DOCX document')
      return
    }

    // Validate file size (max 5MB)
    if (selectedFile.size > 5 * 1024 * 1024) {
      alert('File size should be less than 5MB')
      return
    }

    setFile(selectedFile)
  }

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first')
      return
    }

    setUploading(true)

    try {
      // Prepare profile data for upload
      const profileData = {
        userType: selectedEmploymentType?.title || selectedEmploymentType?.name || 'Guest User',
        fullName: userProfile?.name || '',
        email: userProfile?.email || '',
        phone: userProfile?.phone || ''
      }

      const result = await uploadResumeWithProfile(file, profileData)

      setUploading(false)
      navigate('/personal-info')
    } catch (error) {
      console.error('Upload error:', error)
      alert(error.message || 'Upload failed. Please try again.')
      setUploading(false)
    }
  }

  const handleRemove = () => {
    setFile(null)
  }

  return (
    <div className="cv-upload-container">
      <Navbar userProfile={userProfile} />

      <div className="cv-upload-content">
        <motion.div
          className="upload-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1>Upload Your CV/Resume</h1>
          <p>Upload your resume in PDF or Word format (Max 5MB)</p>
          {selectedEmploymentType && (
            <div className="employment-type-badge">
              Selected: {selectedEmploymentType.title}
            </div>
          )}
        </motion.div>

        <motion.div
          className="upload-area"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
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
                <p className="file-hint">Supported formats: PDF, DOCX</p>
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
                <button className="remove-button" onClick={handleRemove}>
                  ✕
                </button>
              </motion.div>
            )}
          </div>
        </motion.div>

        <motion.div
          className="upload-actions"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <button
            className="back-button"
            onClick={() => navigate('/employment-type')}
          >
            ← Back
          </button>
          <button
            className="continue-button"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Continue →'}
          </button>
        </motion.div>
      </div>
    </div>
  )
}

export default CVUpload

