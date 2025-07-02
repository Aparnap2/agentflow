import { useFlow } from '../contexts/FlowContext'
import { Brain, MessageSquare, CheckCircle, FileText, BarChart3, AlertCircle, Users, Activity, Clock, ChevronDown } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const FlowNavigation = ({ pendingApprovalsCount = 0 }) => {
  const { flowState, navigateToStep } = useFlow()
  const navigate = useNavigate()
  const [showQuickMenu, setShowQuickMenu] = useState(false)
  const menuRef = useRef(null)
  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowQuickMenu(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  const navSteps = [
    { step: 'start', label: 'Start', icon: Brain },
    { step: 'conversation', label: 'Vision', icon: MessageSquare },
    { step: 'tasks', label: 'Tasks', icon: CheckCircle },
    { step: 'outputs', label: 'Outputs', icon: FileText },
    { step: 'reports', label: 'Reports', icon: BarChart3 }
  ]
  
  return (
    <div className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">AgentFlow</span>
          </div>
          
          <div className="flex items-center">
            <div className="flex items-center space-x-1">
              {navSteps.map(({ step, label, icon: Icon }, index) => {
                const isActive = flowState.currentStep === step
                const canNavigate = flowState.canNavigate[step]
                const isCompleted = index > 0 && 
                  navSteps.slice(0, index).every(s => flowState.canNavigate[s.step])
                
                return (
                  <div key={step} className="flex items-center">
                    {index > 0 && (
                      <div className={`h-px w-8 ${isCompleted ? 'bg-primary-500' : 'bg-gray-300'}`}></div>
                    )}
                    <button
                      onClick={() => canNavigate && navigateToStep(step)}
                      disabled={!canNavigate}
                      className={`
                        flex flex-col items-center justify-center p-2 rounded-full
                        ${isActive ? 'text-white bg-primary-600' : 
                          canNavigate ? 'text-primary-600 bg-primary-50 hover:bg-primary-100' : 
                          'text-gray-400 bg-gray-100 cursor-not-allowed'}
                      `}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="text-xs mt-1">{label}</span>
                    </button>
                  </div>
                )
              })}
            </div>
            
            {/* Quick Access Menu */}
            <div className="relative ml-4" ref={menuRef}>
              <button
                onClick={() => setShowQuickMenu(!showQuickMenu)}
                className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
              >
                <span className="text-sm font-medium">More</span>
                <ChevronDown className="h-4 w-4" />
              </button>
              
              {showQuickMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border z-50">
                  <div className="py-1">
                    <button
                      onClick={() => { navigate('/office'); setShowQuickMenu(false) }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Users className="h-4 w-4 mr-3" />
                      Virtual Office
                    </button>
                    <button
                      onClick={() => { navigate('/monitoring'); setShowQuickMenu(false) }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Activity className="h-4 w-4 mr-3" />
                      Monitoring
                    </button>
                    <button
                      onClick={() => { navigate('/history'); setShowQuickMenu(false) }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Clock className="h-4 w-4 mr-3" />
                      History
                    </button>
                    <button
                      onClick={() => { navigate('/agents'); setShowQuickMenu(false) }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <Brain className="h-4 w-4 mr-3" />
                      Agents
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            {/* Approval indicator */}
            {pendingApprovalsCount > 0 && (
              <div className="flex items-center space-x-2 px-3 py-2 bg-orange-100 text-orange-800 rounded-md ml-2">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {pendingApprovalsCount} Approval{pendingApprovalsCount !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FlowNavigation