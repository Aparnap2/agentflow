import { useState, useRef, useEffect } from 'react'
import { Send, CheckCircle, ArrowRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import AgentAvatar from './AgentAvatar'
import { useWorkflow } from '../contexts/WorkflowContext'

const AgentChat = ({ 
  agentName, 
  initialMessages = [], 
  onSendMessage, 
  onApprove = null,
  readyForApproval = false,
  loading = false,
  showApproveButton = false,
  approveButtonText = 'Approve & Continue',
  placeholder = 'Type your message...'
}) => {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const { workflowState, storeAgentConversation } = useWorkflow()
  
  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // Update stored conversation when messages change
  useEffect(() => {
    storeAgentConversation(agentName, messages)
  }, [messages, agentName])
  
  // Send message handler
  const handleSendMessage = async () => {
    if (!input.trim() || loading) return
    
    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    
    if (onSendMessage) {
      const response = await onSendMessage(input)
      if (response) {
        const assistantMessage = { 
          role: 'assistant', 
          content: response.message || response.response || response 
        }
        setMessages(prev => [...prev, assistantMessage])
      }
    }
  }
  
  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }
  
  // Get the active agent's personality name
  const agentPersonalityName = workflowState.agentPersonalities?.[agentName]?.name || agentName
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center p-4 border-b">
        <AgentAvatar agent={agentName} size="sm" showStatus speaking={loading} />
        <div className="ml-3">
          <h3 className="font-semibold text-gray-900">{agentPersonalityName}</h3>
          <p className="text-xs text-gray-500">{agentName} Agent</p>
        </div>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <AgentAvatar agent={agentName} size="lg" />
            <h3 className="text-lg font-medium text-gray-900 mt-4 mb-2">
              Start chatting with {agentPersonalityName}
            </h3>
            <p className="text-gray-600 text-sm">
              {agentName === 'Cofounder' 
                ? 'Tell me about your startup idea and I\'ll help refine your vision'
                : `I'm here to help with ${agentName.toLowerCase()} aspects of your startup`}
            </p>
          </div>
        )}
        
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.role !== 'user' && (
                <div className="mr-2 flex-shrink-0">
                  <AgentAvatar agent={agentName} size="sm" />
                </div>
              )}
              
              <div className={`max-w-[80%] px-4 py-3 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-primary-600 text-white rounded-tr-none' 
                  : 'bg-gray-100 text-gray-900 rounded-tl-none'
              }`}>
                {message.role === 'user' ? (
                  <div className="whitespace-pre-wrap">{message.content}</div>
                ) : (
                  <ReactMarkdown className="prose prose-sm max-w-none">
                    {String(message.content || '')}
                  </ReactMarkdown>
                )}
              </div>
              
              {message.role === 'user' && (
                <div className="ml-2 flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-600 text-xs">You</span>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="mr-2 flex-shrink-0">
                <AgentAvatar agent={agentName} size="sm" pulse={true} />
              </div>
              <div className="bg-gray-100 px-4 py-3 rounded-lg rounded-tl-none">
                <div className="flex items-center space-x-2">
                  <div className="animate-pulse flex space-x-1">
                    <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                    <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                    <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>
      
      {readyForApproval && showApproveButton && (
        <div className="border-t bg-green-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
              <span className="text-green-800 font-medium">Ready for approval!</span>
            </div>
            <button
              onClick={onApprove}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {approveButtonText}
              <ArrowRight className="h-4 w-4 ml-2" />
            </button>
          </div>
        </div>
      )}
      
      <div className="border-t p-4">
        <div className="flex space-x-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows={2}
            disabled={loading || readyForApproval}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || loading || readyForApproval}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default AgentChat