import { Routes, Route } from 'react-router-dom'
import { WorkflowProvider } from './contexts/WorkflowContext'
import WorkflowLayout from './components/WorkflowLayout'
import EnhancedConversationPage from './pages/EnhancedConversationPage'
import ExecutionPage from './pages/ExecutionPage'
import ResultsPage from './pages/ResultsPage'
import DashboardPage from './pages/DashboardPage'
import { useState, useEffect } from 'react'
import api from './lib/api'

function EnhancedApp() {
  const [pendingApprovals, setPendingApprovals] = useState([])
  
  // Poll for pending approvals
  useEffect(() => {
    const pollApprovals = async () => {
      try {
        const data = await api.getPendingApprovals()
        setPendingApprovals(data.approvals || [])
      } catch (error) {
        console.error('Failed to fetch pending approvals:', error)
      }
      } catch (error) {
        console.error('Failed to fetch pending approvals:', error)
      }
    }
    
    // Poll every 5 seconds
    const interval = setInterval(pollApprovals, 5000)
    pollApprovals() // Initial call
    
    return () => clearInterval(interval)
  }, [])

  return (
    <WorkflowProvider>
      <WorkflowLayout>
        <Routes>
          {/* Introduction and Vision Phase */}
          <Route path="/" element={<EnhancedConversationPage />} />
          <Route path="/conversation" element={<EnhancedConversationPage />} />
          
          {/* Execution Phase */}
          <Route path="/execution" element={<ExecutionPage />} />
          
          {/* Results Phase */}
          <Route path="/results" element={<ResultsPage />} />
          
          {/* Dashboard Phase */}
          <Route path="/dashboard" element={<DashboardPage />} />
          
          {/* Fallback to conversation */}
          <Route path="*" element={<EnhancedConversationPage />} />
        </Routes>
      </WorkflowLayout>
    </WorkflowProvider>
  )
}

export default EnhancedApp