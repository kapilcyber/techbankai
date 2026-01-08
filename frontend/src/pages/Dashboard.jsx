import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import Navbar from '../components/Navbar'
import EmploymentIcon from '../components/EmploymentIcon'
import IDVerificationModal from '../components/IDVerificationModal'
import './Dashboard.css'

const Dashboard = () => {
  const [selectedType, setSelectedType] = useState(null)
  const [hoveredType, setHoveredType] = useState(null)
  const [showVerificationModal, setShowVerificationModal] = useState(false)
  const [selectedEmploymentTypeForVerification, setSelectedEmploymentTypeForVerification] = useState(null)
  const navigate = useNavigate()
  const { setSelectedEmploymentType, userProfile } = useApp()

  const employmentTypes = [
    {
      id: 'company-employee',
      title: 'Company Employee',
      description: 'Full-time or part-time employee at a company',
      color: '#3282b8'
    },
    {
      id: 'freelancer',
      title: 'Freelancer',
      description: 'Independent contractor or self-employed',
      color: '#bbe1fa'
    },
    {
      id: 'guest-user',
      title: 'Guest User',
      description: 'Temporary or guest access',
      color: '#0f4c75'
    }
  ]

  const handleTypeSelect = (type) => {
    setSelectedType(type.id)

    // Check if this employment type requires ID verification
    const requiresVerification = type.id === 'company-employee' ||
      type.id === 'freelancer'

    if (requiresVerification) {
      // Show verification modal
      setSelectedEmploymentTypeForVerification(type)
      setShowVerificationModal(true)
      console.log('Verification required for:', type.title, 'User Profile:', userProfile)
    } else {
      // Guest User - no verification needed
      setSelectedEmploymentType(type)
      setTimeout(() => {
        navigate('/application')
      }, 500)
    }
  }

  const handleVerificationSuccess = () => {
    setShowVerificationModal(false)
    setSelectedEmploymentType(selectedEmploymentTypeForVerification)
    setTimeout(() => {
      navigate('/application')
    }, 300)
  }

  const handleVerificationClose = () => {
    setShowVerificationModal(false)
    setSelectedType(null)
    setSelectedEmploymentTypeForVerification(null)
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const cardVariants = {
    hidden: { opacity: 0, y: 50, scale: 0.9 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 100
      }
    }
  }

  return (
    <div className="dashboard-container">
      <div className="animated-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
        <div className="gradient-orb orb-4"></div>
      </div>

      <Navbar userProfile={userProfile} />

      <div className="dashboard-content">
        <motion.div
          className="dashboard-hero"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="hero-glass"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h1>Select Your Employment Type</h1>
            <p>Choose the option that best describes your current employment status</p>
          </motion.div>
        </motion.div>

        <motion.div
          className="employment-types-grid"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {employmentTypes.map((type) => (
            <motion.div
              key={type.id}
              className={`employment-type-card ${selectedType === type.id ? 'selected' : ''}`}
              variants={cardVariants}
              whileHover={{
                scale: 1.05,
                y: -10,
                transition: { duration: 0.2 }
              }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleTypeSelect(type)}
              onMouseEnter={() => setHoveredType(type.id)}
              onMouseLeave={() => setHoveredType(null)}
              style={{
                '--type-color': type.color,
                '--type-color-rgb': type.color === '#3282b8' ? '50, 130, 184' :
                  type.color === '#bbe1fa' ? '187, 225, 250' :
                    '15, 76, 117',
                '--hover-bg-start': type.id === 'company-employee' ? 'rgba(50, 130, 184, 0.25)' :
                  type.id === 'freelancer' ? 'rgba(187, 225, 250, 0.3)' :
                    'rgba(15, 76, 117, 0.25)',
                '--hover-bg-end': type.id === 'company-employee' ? 'rgba(255, 255, 255, 0.85)' :
                  type.id === 'freelancer' ? 'rgba(255, 255, 255, 0.9)' :
                    'rgba(255, 255, 255, 0.85)'
              }}
            >
              <EmploymentIcon
                type={type.id}
                isHovered={hoveredType === type.id}
              />

              <h2>{type.title}</h2>
              <p>{type.description}</p>

              <motion.div
                className="selection-indicator"
                initial={{ scale: 0 }}
                animate={{
                  scale: selectedType === type.id ? 1 : 0,
                  opacity: selectedType === type.id ? 1 : 0
                }}
                transition={{ type: "spring", stiffness: 200 }}
              >
                ✓ Selected
              </motion.div>
            </motion.div>
          ))}
        </motion.div>

        {selectedType && !showVerificationModal && (
          <motion.div
            className="continue-hint"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p>Redirecting to application page...</p>
          </motion.div>
        )}
      </div>

      <IDVerificationModal
        isOpen={showVerificationModal}
        onClose={handleVerificationClose}
        onVerify={handleVerificationSuccess}
        employmentType={selectedEmploymentTypeForVerification}
        userProfile={userProfile}
      />
    </div>
  )
}

export default Dashboard

