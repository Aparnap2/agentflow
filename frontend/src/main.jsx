import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import ChatOnboarding from './components/ChatOnboarding.jsx'
import EnhancedDashboard from './components/EnhancedDashboard.jsx'
import EnhancedWorkflowPage from './pages/EnhancedWorkflowPage.jsx'
import EnhancedResultsPage from './pages/EnhancedResultsPage.jsx'
import './index.css'

// Create root element
const root = ReactDOM.createRoot(document.getElementById('root'))

// Render the app with PRD-compliant routing
// PRD Section 3.1: Users access SPA and enter chat interface
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<ChatOnboarding />} />
        <Route path="/dashboard" element={<EnhancedDashboard />} />
        <Route path="/enhanced-workflow" element={<EnhancedWorkflowPage />} />
        <Route path="/enhanced-results" element={<EnhancedResultsPage />} />
        <Route path="/app" element={<App />} />
      </Routes>
    </Router>
  </React.StrictMode>
)
