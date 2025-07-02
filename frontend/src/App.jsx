import { Routes, Route } from 'react-router-dom'
import { FlowProvider } from './contexts/FlowContext'
import StartPage from './pages/StartPage'
import ConversationPage from './pages/ConversationPage'
import TasksPage from './pages/TasksPage'
import VirtualOfficePage from './pages/VirtualOfficePage'
import VisionPage from './pages/VisionPage'
import AgentsPage from './pages/AgentsPage'
import DashboardPage from './pages/DashboardPage'
import AnalyticsPage from './pages/AnalyticsPage'
import OutputsPage from './pages/OutputsPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'
import Navigation from './components/Navigation'
import ApprovalModal from './components/ApprovalModal'
import { useState, useEffect } from 'react'
import { api } from './lib/api'

function App() {
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  const [currentApproval, setCurrentApproval] = useState(null)

  // Poll for pending approvals
  useEffect(() => {
    const pollApprovals = async () => {
      try {
        const response = await api.get('/approvals/pending')
        const approvals = response.data.approvals || []
        setPendingApprovals(approvals)
        
        // Show modal for first pending approval
        if (approvals.length > 0 && !showApprovalModal) {
          setCurrentApproval(approvals[0])
          setShowApprovalModal(true)
        }
      } catch (error) {
        console.error('Failed to fetch pending approvals:', error)
      }
    }

    // Poll every 5 seconds
    const interval = setInterval(pollApprovals, 5000)
    pollApprovals() // Initial call

    return () => clearInterval(interval)
  }, [showApprovalModal])

  const handleApprovalResponse = async (approvalId, action, feedback) => {
    try {
      await api.post(`/approvals/${approvalId}/respond`, {
        action,
        feedback
      })
      
      // Remove from pending list
      setPendingApprovals(prev => prev.filter(a => a.id !== approvalId))
      setShowApprovalModal(false)
      setCurrentApproval(null)
      
      // Show next approval if any
      const remaining = pendingApprovals.filter(a => a.id !== approvalId)
      if (remaining.length > 0) {
        setCurrentApproval(remaining[0])
        setShowApprovalModal(true)
      }
    } catch (error) {
      console.error('Failed to respond to approval:', error)
    }
  }

  return (
    <FlowProvider>
      <div className="min-h-screen bg-gray-50">
        <Navigation pendingApprovalsCount={pendingApprovals.length} />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/start" element={<StartPage />} />
            <Route path="/chat" element={<ConversationPage />} />
            <Route path="/conversation" element={<ConversationPage />} />
            <Route path="/vision" element={<VisionPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/outputs" element={<OutputsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/office" element={<VirtualOfficePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
        
        {/* Approval Modal */}
        {showApprovalModal && currentApproval && (
          <ApprovalModal
            approval={currentApproval}
            onResponse={handleApprovalResponse}
            onClose={() => setShowApprovalModal(false)}
          />
        )}
      </div>
    </FlowProvider>
  )
}

export default App