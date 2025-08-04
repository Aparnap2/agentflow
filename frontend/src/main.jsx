import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import EnhancedWorkflowPage from './pages/EnhancedWorkflowPage.jsx'
import EnhancedResultsPage from './pages/EnhancedResultsPage.jsx'
import './index.css'

// Create root element
const root = ReactDOM.createRoot(document.getElementById('root'))

// Render the app with authentication-first routing
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/enhanced-workflow" element={<EnhancedWorkflowPage />} />
        <Route path="/enhanced-results" element={<EnhancedResultsPage />} />
      </Routes>
    </Router>
  </React.StrictMode>
)
