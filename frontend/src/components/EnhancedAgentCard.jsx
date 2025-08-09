import { useState, useEffect } from 'react'
import { Brain, Users, Target, DollarSign, Megaphone, Scale, Clock, CheckCircle, AlertCircle, Loader, Play, Pause, Square, Star } from 'lucide-react'
import api from '../lib/api'

const EnhancedAgentCard = ({ agent, onAction }) => {
  const [personality, setPersonality] = useState(null)
  
  // Fetch agent personalities
  useEffect(() => {
    const fetchPersonalities = async () => {
      try {
        const response = await api.get('/agents/personalities')
        if (response.status === 200) {
          const personalities = response.data
          setPersonality(personalities[agent.name])
        }
      } catch (error) {
        console.error('Failed to fetch personalities:', error)
      }
    }
    
    fetchPersonalities()
  }, [agent.name])
  
  const icons = {
    Cofounder: Brain,
    Manager: Users, 
    Product: Target,
    Finance: DollarSign,
    Marketing: Megaphone,
    Legal: Scale
  }
  
  const statusColors = {
    idle: 'bg-gray-100 text-gray-600',
    thinking: 'bg-yellow-100 text-yellow-700',
    working: 'bg-blue-100 text-blue-700', 
    waiting_approval: 'bg-orange-100 text-orange-700',
    completed: 'bg-green-100 text-green-700',
    error: 'bg-red-100 text-red-700'
  }
  
  const Icon = icons[agent.name] || Brain
  const StatusIcon = agent.status === 'working' ? Loader : 
                    agent.status === 'completed' ? CheckCircle :
                    agent.status === 'error' ? AlertCircle : Clock
  
  // Get personality name or default to agent name
  const agentName = personality?.name || agent.name
  const avatarEmoji = personality?.avatar_emoji || null
  
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center mr-4 text-xl">
            {avatarEmoji || <Icon className="h-6 w-6 text-primary-600" />}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{agentName}</h3>
            <p className="text-sm text-gray-600">{agent.role}</p>
            {personality?.background && (
              <p className="text-xs text-gray-500 mt-1 max-w-xs truncate">
                {personality.background}
              </p>
            )}
          </div>
        </div>
        
        <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColors[agent.status]}`}>
          <StatusIcon className={`h-4 w-4 mr-1 ${agent.status === 'working' ? 'animate-spin' : ''}`} />
          {agent.status.replace('_', ' ')}
        </div>
      </div>
      
      {/* Personality Traits */}
      {personality?.traits && (
        <div className="mb-3">
          <div className="flex items-center mb-2">
            <Brain className="h-4 w-4 text-gray-500 mr-2" />
            <span className="text-sm font-medium text-gray-700">Traits</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {personality.traits.slice(0, 3).map((trait, index) => (
              <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                {trait.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Expertise Areas */}
      {personality?.expertise_areas && (
        <div className="mb-4">
          <div className="flex items-center mb-2">
            <Star className="h-4 w-4 text-gray-500 mr-2" />
            <span className="text-sm font-medium text-gray-700">Expertise</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {personality.expertise_areas.slice(0, 2).map((area, index) => (
              <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                {area.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {agent.current_task && (
        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-700">{agent.current_task}</p>
        </div>
      )}
      
      <div className="flex space-x-2">
        {agent.status === 'idle' && (
          <button onClick={() => onAction(agent.name, 'start')} className="flex items-center px-3 py-1 bg-green-600 text-white rounded text-sm">
            <Play className="h-3 w-3 mr-1" /> Start
          </button>
        )}
        {agent.status === 'working' && (
          <button onClick={() => onAction(agent.name, 'pause')} className="flex items-center px-3 py-1 bg-yellow-600 text-white rounded text-sm">
            <Pause className="h-3 w-3 mr-1" /> Pause
          </button>
        )}
        {agent.status !== 'idle' && (
          <button onClick={() => onAction(agent.name, 'stop')} className="flex items-center px-3 py-1 bg-red-600 text-white rounded text-sm">
            <Square className="h-3 w-3 mr-1" /> Stop
          </button>
        )}
      </div>
      
      {/* Working Style */}
      {personality?.working_style && (
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <p className="text-xs text-gray-600 italic">
            "{personality.working_style}"
          </p>
        </div>
      )}
    </div>
  )
}

export default EnhancedAgentCard