import { useWorkflow } from '../contexts/WorkflowContext'
import WorkflowSidebar from './WorkflowSidebar'
import AgentTransition from './AgentTransition'

const WorkflowLayout = ({ children }) => {
  const { workflowState } = useWorkflow()
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <WorkflowSidebar />
      
      {/* Main content */}
      <div className={`
        ${workflowState.showSidebar ? 'ml-64' : 'ml-16'} 
        transition-all duration-300 ease-in-out
        min-h-screen
      `}>
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </div>
      
      {/* Agent transition overlay */}
      {workflowState.showAgentTransition && (
        <AgentTransition 
          fromAgent={workflowState.activeAgent}
          toAgent={workflowState.transitionAgent}
        />
      )}
    </div>
  )
}

export default WorkflowLayout