import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Brain, ArrowRight, Lightbulb } from 'lucide-react'
import { api } from '../lib/api'

const StartPage = () => {
  const [vision, setVision] = useState('')
  const [userName, setUserName] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!vision.trim()) return
    
    setLoading(true)
    try {
      const response = await api.post('/start-project', {
        vision: vision.trim(),
        user_name: userName.trim() || 'User',
        approval_mode: 'manual'
      })
      
      if (response.data.status === 'started') {
        navigate('/vision')
      }
    } catch (error) {
      console.error('Failed to start project:', error)
      alert('Failed to start project. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-primary-100 rounded-full">
            <Brain className="h-12 w-12 text-primary-600" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to AgentFlow
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your virtual AI office where intelligent agents collaborate to bring your startup vision to life
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm border p-8">
        <div className="flex items-center mb-6">
          <Lightbulb className="h-6 w-6 text-yellow-500 mr-3" />
          <h2 className="text-2xl font-semibold text-gray-900">
            Share Your Vision
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="userName" className="block text-sm font-medium text-gray-700 mb-2">
              Your Name (Optional)
            </label>
            <input
              type="text"
              id="userName"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="Enter your name"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label htmlFor="vision" className="block text-sm font-medium text-gray-700 mb-2">
              Project Vision *
            </label>
            <textarea
              id="vision"
              value={vision}
              onChange={(e) => setVision(e.target.value)}
              placeholder="Describe your startup idea, target users, and what problem you're solving..."
              rows={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              required
            />
            <p className="text-sm text-gray-500 mt-2">
              Be as detailed as possible. Our AI agents will use this to create your complete startup plan.
            </p>
          </div>
          
          <button
            type="submit"
            disabled={!vision.trim() || loading}
            className="w-full flex items-center justify-center px-6 py-3 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                Starting Your Virtual Office...
              </div>
            ) : (
              <div className="flex items-center">
                Start Project
                <ArrowRight className="h-5 w-5 ml-2" />
              </div>
            )}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-gray-600 mb-4">Or start with a conversation</p>
          <button
            onClick={() => navigate('/chat')}
            className="px-6 py-2 border border-primary-600 text-primary-600 rounded-md hover:bg-primary-50 transition-colors"
          >
            Chat with AI Cofounder
          </button>
        </div>
      </div>
      
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="text-center p-6">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🧠</span>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">AI Cofounder</h3>
          <p className="text-sm text-gray-600">Captures and refines your vision</p>
        </div>
        
        <div className="text-center p-6">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🧭</span>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">AI Manager</h3>
          <p className="text-sm text-gray-600">Creates roadmap and assigns tasks</p>
        </div>
        
        <div className="text-center p-6">
          <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">👥</span>
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">Specialist Team</h3>
          <p className="text-sm text-gray-600">Product, Finance, Marketing & Legal experts</p>
        </div>
      </div>
    </div>
  )
}

export default StartPage