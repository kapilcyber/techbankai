import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import Navbar from '../components/Navbar'
import './EmploymentTypeSelection.css'

const EmploymentTypeSelection = () => {
  const [selectedType, setSelectedType] = useState(null)
  const [hoveredType, setHoveredType] = useState(null)
  const navigate = useNavigate()
  const { setSelectedEmploymentType, userProfile } = useApp()

  const employmentTypes = [
    {
      id: 'company-employee',
      title: 'Company Employee',
      icon: '🏢',
      description: 'Full-time or part-time employee at a company',
      color: '#667eea'
    },

    {
      id: 'freelancer',
      title: 'Freelancer',
      icon: '💼',
      description: 'Independent contractor or self-employed',
      color: '#4facfe'
    },
    {
      id: 'guest-user',
      title: 'Guest User',
      icon: '👤',
      description: 'Temporary or guest access',
      color: '#43e97b'
    }
  ]

  const handleTypeSelect = (type) => {
    setSelectedType(type.id)
    setSelectedEmploymentType(type)

    // Navigate to CV upload after a short delay for animation
    setTimeout(() => {
      navigate('/upload-cv')
    }, 500)
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
    <div className="employment-selection-container">
      <Navbar userProfile={userProfile} />

      <div className="employment-selection-content">
        <motion.div
          className="selection-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1>Select Your Employment Type</h1>
          <p>Choose the option that best describes your current employment status</p>
        </motion.div>

        <motion.div
          className="employment-types-grid"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {employmentTypes.map((type, index) => (
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
                '--hover-scale': hoveredType === type.id ? 1.05 : 1
              }}
            >
              <motion.div
                className="type-icon"
                animate={{
                  rotate: hoveredType === type.id ? [0, -10, 10, -10, 0] : 0,
                  scale: hoveredType === type.id ? 1.2 : 1
                }}
                transition={{ duration: 0.5 }}
              >
                {type.icon}
              </motion.div>

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

        {selectedType && (
          <motion.div
            className="continue-hint"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p>Redirecting to upload page...</p>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default EmploymentTypeSelection

