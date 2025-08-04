import React from 'react'
import { Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import StartPage from './pages/StartPage'
import ConversationPage from './pages/ConversationPage'
import AgentsPage from './pages/AgentsPage'
import Navigation from './components/Navigation'

// Simple version of the enhanced app without complex hooks
function SimpleEnhancedApp() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/start" element={<StartPage />} />
          <Route path="/chat" element={<ConversationPage />} />
          <Route path="/conversation" element={<ConversationPage />} />
          <Route path="/agents" element={<AgentsPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default SimpleEnhancedApp