import { useState } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import Navbar from '../components/Navbar'
import AdminDashboard from '../components/admin/AdminDashboard'
import SearchTalent from '../components/admin/SearchTalent'
import SearchUsingJD from '../components/admin/SearchUsingJD'
import AddNewResume from '../components/admin/AddNewResume'
import './Admin.css'

const Admin = () => {
  const { userProfile } = useApp()
  const [activeTab, setActiveTab] = useState('dashboard')

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊', colorClass: 'tab-dashboard' },
    { id: 'search-talent', label: 'Search Talent', icon: '🔍', colorClass: 'tab-search-talent' },
    { id: 'search-jd', label: 'Search Using JD', icon: '📝', colorClass: 'tab-search-jd' },
    { id: 'add-resume', label: 'Add New Resume', icon: '➕', colorClass: 'tab-add-resume' }
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <AdminDashboard />
      case 'search-talent':
        return <SearchTalent />
      case 'search-jd':
        return <SearchUsingJD />
      case 'add-resume':
        return <AddNewResume />
      default:
        return <AdminDashboard />
    }
  }

  return (
    <div className="admin-container">
      <Navbar userProfile={userProfile} showProfile={false} />

      <div className="admin-content">
        <motion.div
          className="admin-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1>Admin Panel</h1>
          <p>Manage applications, search talent, and analyze data</p>
        </motion.div>

        <div className="admin-tabs">
          {tabs.map((tab) => (
            <motion.button
              key={tab.id}
              className={`admin-tab ${tab.colorClass} ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: tabs.indexOf(tab) * 0.1 }}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </motion.button>
          ))}
        </div>

        <motion.div
          className="admin-content-area"
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {renderContent()}
        </motion.div>
      </div>
    </div>
  )
}

export default Admin

