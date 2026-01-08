import { motion } from 'framer-motion'

const EmploymentIcon = ({ type, isHovered }) => {
  const iconConfig = {
    'company-employee': {
      emoji: '🏛️',
      unicode: '◉',
      className: 'icon-building'
    },
    'hired-forces': {
      emoji: '⚡',
      unicode: '◆',
      className: 'icon-forces'
    },
    'freelancer': {
      emoji: '💡',
      unicode: '▲',
      className: 'icon-freelancer'
    },
    'guest-user': {
      emoji: '⭐',
      unicode: '★',
      className: 'icon-guest'
    }
  }

  const config = iconConfig[type] || iconConfig['company-employee']

  return (
    <div className={`icon-container ${config.className}`}>
      <motion.span
        className="icon-main"
        animate={{
          rotate: isHovered ? [0, -15, 15, -15, 0] : 0,
          scale: isHovered ? 1.3 : 1,
          y: isHovered ? [0, -8, 0] : 0
        }}
        transition={{
          duration: 0.6,
          repeat: isHovered ? Infinity : 0,
          repeatType: "reverse"
        }}
      >
        {config.emoji}
      </motion.span>
      <motion.div
        className="icon-particles"
        animate={{
          scale: isHovered ? [1, 1.2, 1] : 1,
          opacity: isHovered ? [0.3, 0.6, 0.3] : 0
        }}
        transition={{
          duration: 2,
          repeat: isHovered ? Infinity : 0
        }}
      >
        <span className="particle particle-1"></span>
        <span className="particle particle-2"></span>
        <span className="particle particle-3"></span>
        <span className="particle particle-4"></span>
      </motion.div>
    </div>
  )
}

export default EmploymentIcon

