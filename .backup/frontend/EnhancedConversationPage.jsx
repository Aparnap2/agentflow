import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkflow } from '../contexts/WorkflowContext'
import AgentChat from '../components/AgentChat'
import AgentAvatar from '../components/AgentAvatar'
import { Brain, ArrowRight, Users, Target, DollarSign, Megaphone, Scale } from 'lucide-react'
import api from '../lib/api'

const EnhancedConversationPage = () => {
  const [loading, setLoading] = useState(false)
  const [readyForApproval, setReadyForApproval] = useState(false)
  const navigate = useNavigate()
  
  const { 
    workflowState, 
    updateWorkflowState, 
    nextPhase,
    transitionToAgent
  } = useWorkflow()
  
  // Get stored conversation for the active agent
  const activeAgentConversation = workflowState.agentConversations[workflowState.activeAgent] || []
  
  // Send message to the active agent
  const sendMessage = async (message) => {
    setLoading(true)
    
    try {
      let response
      
      if (!workflowState.conversationId) {
        // Start new conversation
        response = await api.startConversation(message)
        
        // Update workflow state with conversation ID
        updateWorkflowState({ 
          conversationId: response.conversation_id,
          currentPhase: 'vision'
        })
      } else {
        // Continue conversation
        response = await api.sendMessage(workflowState.conversationId, message)
      }
      
      // Check if vision is ready for approval
      if (response.ready_for_approval) {
        setReadyForApproval(true)
      }
      
      return response
    } catch (error) {
      console.error('Failed to send message:', error)
      return { message: 'Sorry, I encountered an error. Please try again.' }
    } finally {
      setLoading(false)
    }
  }
  
  // Approve vision and proceed to next phase
  const approveAndProceed = async () => {
    if (!workflowState.conversationId) return
    
    setLoading(true)
    try {
      const response = await api.approveConversation(workflowState.conversationId)
      
      // Update workflow state
      updateWorkflowState({ 
        visionApproved: true,
        projectId: response.project_id,
        tasksDistributed: true
      })
      
      // Transition to Manager agent
      transitionToAgent('Manager')
      
      // Move to next phase
      nextPhase()
    } catch (error) {
      console.error('Failed to approve conversation:', error)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {workflowState.currentPhase === 'introduction' ? 'Welcome to AgentFlow' : 'Refine Your Vision'}
        </h1>
        <p className="text-gray-600">
          {workflowState.currentPhase === 'introduction' 
            ? 'Chat with our AI Cofounder to bring your startup idea to life'
            : 'Discuss your startup idea with our AI Cofounder to refine your vision'}
        </p>
      </div>
      
      {workflowState.currentPhase === 'introduction' && (
        <div className="bg-white rounded-lg shadow-sm border p-8 mb-8">
          <div className="flex items-center mb-6">
            <Brain className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">
              Meet Your AI Team
            </h2>
          </div>
          
          <p className="text-gray-600 mb-6">
            AgentFlow provides you with a complete AI team to help bring your startup idea to life. 
            Each agent has a unique personality and expertise to assist with different aspects of your business.
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
            {['Cofounder', 'Manager', 'Product', 'Finance', 'Marketing', 'Legal'].map(agentName => (
              <div 
                key={agentName}
                className="flex flex-col items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                onClick={() => transitionToAgent(agentName)}
              >
                <AgentAvatar agent={agentName} size="md" />
                <h3 className="font-semibold text-gray-900 mt-3">{agentName}</h3>
              </div>
            ))}
          </div>
          
          <div className="flex justify-center">
            <button
              onClick={() => {
                transitionToAgent('Cofounder')
                updateWorkflowState({ currentPhase: 'vision' })
              }}
              className="flex items-center px-6 py-3 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              Start with Cofounder
              <ArrowRight className="h-5 w-5 ml-2" />
            </button>
          </div>
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden h-[calc(100vh-12rem)]">
        <AgentChat
          agentName={workflowState.activeAgent}
          initialMessages={activeAgentConversation}
          onSendMessage={sendMessage}
          onApprove={approveAndProceed}
          readyForApproval={readyForApproval}
          loading={loading}
          showApproveButton={readyForApproval}
          approveButtonText="Approve Vision & Continue"
          placeholder={
            workflowState.activeAgent === 'Cofounder'
              ? 'Describe your startup idea...'
              : `Ask ${workflowState.activeAgent} about your startup...`
          }
        />
      </div>
    </div>
  )
}

export default EnhancedConversationPage