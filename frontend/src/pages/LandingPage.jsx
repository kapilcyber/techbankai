import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import './LandingPage.css'

const LandingPage = () => {
    const navigate = useNavigate()

    return (
        <div className="landing-container">
            <div className="animated-background">
                <div className="gradient-orb orb-1"></div>
                <div className="gradient-orb orb-2"></div>
                <div className="gradient-orb orb-3"></div>
            </div>

            <motion.div
                className="content-wrapper"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
            >
                <h1 className="main-title">TechBank.Ai</h1>
                <p className="subtitle">Advanced Resume Screening & Management Platform</p>

                <div className="portal-cards">
                    <motion.div
                        className="portal-card user-card"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/login')}
                    >
                        <div className="card-icon">👤</div>
                        <h2>User Portal</h2>
                        <p>For Candidates, Employees & Freelancers</p>
                        <button className="enter-btn">Enter User Portal</button>
                    </motion.div>

                    <motion.div
                        className="portal-card admin-card"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/login?admin=true')}
                    >
                        <div className="card-icon">🛡️</div>
                        <h2>Admin Portal</h2>
                        <p>For HR Managers & Administrators</p>
                        <button className="enter-btn">Enter Admin Portal</button>
                    </motion.div>
                </div>
            </motion.div>
        </div>
    )
}

export default LandingPage
