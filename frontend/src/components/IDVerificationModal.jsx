import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import './IDVerificationModal.css'

const IDVerificationModal = ({ isOpen, onClose, onVerify, employmentType, userProfile }) => {
  const [enteredId, setEnteredId] = useState('')
  const [error, setError] = useState('')
  const [isVerifying, setIsVerifying] = useState(false)

  // Debug log
  if (isOpen) {
    console.log('ID Verification Modal is open', { employmentType, userProfile })
  }

  const getStoredId = () => {
    if (employmentType?.id === 'company-employee') {
      return userProfile?.employeeId || ''
    } else if (employmentType?.id === 'freelancer') {
      return userProfile?.freelancerId || ''
    }
    return ''
  }

  const getFieldLabel = () => {
    if (employmentType?.id === 'company-employee') {
      return 'Employee ID'
    } else if (employmentType?.id === 'freelancer') {
      return 'ID'
    }
    return 'ID'
  }

  const handleVerify = () => {
    setError('')

    if (!enteredId.trim()) {
      setError(`${getFieldLabel()} is required`)
      return
    }

    setIsVerifying(true)
    const storedId = getStoredId()

    // Debug logging
    console.log('Verification attempt:', {
      employmentType: employmentType?.id,
      enteredId: enteredId.trim(),
      storedId: storedId.trim(),
      userProfile: userProfile
    })

    // Simulate verification delay
    setTimeout(() => {
      setIsVerifying(false)

      if (enteredId.trim() === storedId.trim()) {
        onVerify()
      } else {
        setError(`${getFieldLabel()} does not match. Please try again.`)
        console.error('ID mismatch:', {
          entered: enteredId.trim(),
          stored: storedId.trim(),
          employmentType: employmentType?.id
        })
      }
    }, 500)
  }

  const handleClose = () => {
    setEnteredId('')
    setError('')
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="id-verification-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
        >
          <motion.div
            className="id-verification-modal"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.3 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="verification-modal-header">
              <h2>Verify Your {getFieldLabel()}</h2>
              <button className="verification-close-button" onClick={handleClose}>
                ×
              </button>
            </div>

            <div className="verification-modal-content">
              <p className="verification-modal-description">
                Please enter your {getFieldLabel().toLowerCase()} to continue as <strong>{employmentType?.title}</strong>
              </p>

              <div className="verification-form-group">
                <label htmlFor="verificationId">
                  {getFieldLabel()} <span className="required">*</span>
                </label>
                <div className="input-wrapper">
                  <input
                    type="text"
                    id="verificationId"
                    value={enteredId}
                    onChange={(e) => {
                      setEnteredId(e.target.value)
                      setError('')
                    }}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleVerify()
                      }
                    }}
                    placeholder={`Enter your ${getFieldLabel().toLowerCase()}`}
                    className={error ? 'error' : ''}
                    autoComplete="off"
                    autoFocus
                  />
                  {isVerifying && (
                    <div className="verification-loader">
                      <div className="spinner"></div>
                    </div>
                  )}
                </div>
                {error && <span className="error-message">{error}</span>}
              </div>
            </div>

            <div className="verification-modal-actions">
              <button
                className="verification-btn-cancel"
                onClick={handleClose}
                disabled={isVerifying}
              >
                Cancel
              </button>
              <button
                className="verification-btn-verify"
                onClick={handleVerify}
                disabled={!enteredId.trim() || isVerifying}
              >
                {isVerifying ? 'Verifying...' : 'Verify'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default IDVerificationModal

