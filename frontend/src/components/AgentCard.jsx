import { Brain, Users, Target, DollarSign, Megaphone, Scale, Clock, CheckCircle, AlertCircle, Loader, Play, Pause, Square } from 'lucide-react'

const AgentCard = ({ agent, onAction }) => {
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
  
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className="p-2 bg-blue-100 rounded-lg mr-3">
            <Icon className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{agent.name}</h3>
            <p className="text-sm text-gray-600">{agent.role}</p>
          </div>
        </div>
        
        <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColors[agent.status]}`}>
          <StatusIcon className={`h-4 w-4 mr-1 ${agent.status === 'working' ? 'animate-spin' : ''}`} />
          {agent.status.replace('_', ' ')}
        </div>
      </div>
      
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
    </div>
  )
}

export default AgentCard