import { useState, useRef, useEffect } from 'react'
import { Send, Brain, CheckCircle, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { useFlow } from '../contexts/FlowContext'
import api from '../lib/api'

const ConversationPage = () => {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [readyForApproval, setReadyForApproval] = useState(false)
  const messagesEndRef = useRef(null)
  const navigate = useNavigate()
  const { updateFlowState } = useFlow()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      let response
      if (!conversationId) {
        response = await api.startConversation(input)
        setConversationId(response.conversation_id)
        updateFlowState({ 
          conversationId: response.conversation_id,
          currentStep: 'conversation'
        })
      } else {
        response = await api.sendMessage(conversationId, input)
        console.log('Frontend received response:', response)
      }

      const assistantMessage = { role: 'assistant', content: response.response }
      console.log('Assistant message being added:', assistantMessage)
      setMessages(prev => [...prev, assistantMessage])
      setReadyForApproval(response.ready_for_approval)
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const approveAndProceed = async () => {
    if (!conversationId) return

    setLoading(true)
    try {
      const response = await api.approveConversation(conversationId)
      updateFlowState({ 
        visionApproved: true,
        projectId: response.project_id,
        tasksDistributed: true
      })
      navigate('/tasks', { state: { projectId: response.project_id, tasks: response.tasks } })
    } catch (error) {
      console.error('Failed to approve conversation:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      <div className="mb-6">
        <div className="flex items-center mb-4">
          <Brain className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Chat with AI Cofounder</h1>
            <p className="text-gray-600">Discuss your startup idea to refine your vision</p>
          </div>
        </div>
      </div>

      <div className="flex-1 bg-white rounded-lg shadow-sm border flex flex-col">
        <div className="flex-1 p-6 overflow-y-auto">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Start Your Conversation</h3>
              <p className="text-gray-600">Tell me about your startup idea and I'll help refine your vision</p>
            </div>
          )}

          <div className="space-y-4">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl px-4 py-3 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-primary-600 text-white' 
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  {message.role === 'user' ? (
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  ) : (
                    <ReactMarkdown>{String(message.content || '')}</ReactMarkdown>
                  )}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                    <span className="text-gray-600">AI Cofounder is thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
          <div ref={messagesEndRef} />
        </div>

        {readyForApproval && (
          <div className="border-t bg-green-50 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                <span className="text-green-800 font-medium">Vision is ready for approval!</span>
              </div>
              <button
                onClick={approveAndProceed}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                Approve & Proceed
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
              placeholder="Describe your startup idea..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              rows={2}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConversationPage