import { useState, useEffect } from 'react'
import { Brain, Users, Target, DollarSign, Megaphone, Scale, Briefcase, Wrench } from 'lucide-react'

const AgentAvatar = ({ 
  agent, 
  size = 'md', 
  showStatus = false, 
  pulse = false,
  speaking = false,
  onClick = null
}) => {
  const [personalities, setPersonalities] = useState({})
  
  // Fetch agent personalities
  useEffect(() => {
    const fetchPersonalities = async () => {
      try {
        const response = await fetch('/api/agents/personalities')
        if (response.ok) {
          const data = await response.json()
          setPersonalities(data)
        }
      } catch (error) {
        console.error('Failed to fetch personalities:', error)
      }
    }
    
    fetchPersonalities()
  }, [])
  
  // Default agent icons
  const agentIcons = {
    Cofounder: Brain,
    Manager: Users,
    Product: Target,
    Finance: DollarSign,
    Marketing: Megaphone,
    Legal: Scale,
    Sales: Briefcase,
    Operations: Wrench
  }
  
  // Status colors
  const statusColors = {
    idle: 'bg-gray-100',
    thinking: 'bg-yellow-100',
    working: 'bg-blue-100',
    waiting: 'bg-orange-100',
    completed: 'bg-green-100',
    error: 'bg-red-100'
  }
  
  // Size classes
  const sizeClasses = {
    sm: 'w-8 h-8 text-lg',
    md: 'w-12 h-12 text-xl',
    lg: 'w-16 h-16 text-2xl',
    xl: 'w-20 h-20 text-3xl'
  }
  
  // Get agent personality
  const personality = personalities[agent] || {}
  const Icon = agentIcons[agent] || Brain
  const status = agent?.status || 'idle'
  const statusColor = statusColors[status] || statusColors.idle
  
  // Get avatar emoji or use icon
  const avatarEmoji = personality?.avatar_emoji
  
  return (
    <div 
      className={`relative ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div 
        className={`
          ${sizeClasses[size]} 
          ${speaking ? 'ring-2 ring-primary-500 ring-offset-2' : ''}
          ${pulse ? 'animate-pulse' : ''}
          rounded-full flex items-center justify-center
          bg-gradient-to-br from-primary-100 to-primary-200
          transition-all duration-300 ease-in-out
        `}
      >
        {avatarEmoji ? (
          <span>{avatarEmoji}</span>
        ) : (
          <Icon className="w-1/2 h-1/2 text-primary-600" />
        )}
      </div>
      
      {showStatus && (
        <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full ${statusColor} border-2 border-white`}></div>
      )}
    </div>
  )
}

export default AgentAvatar