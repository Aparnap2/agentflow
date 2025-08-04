import { CheckCircle, Clock, AlertCircle, Loader, XCircle } from 'lucide-react'

const StatusIndicator = ({ status, size = 'sm', showText = true }) => {
  const configs = {
    idle: { icon: Clock, color: 'text-gray-500 bg-gray-100', text: 'Idle' },
    working: { icon: Loader, color: 'text-blue-600 bg-blue-100', text: 'Working', animate: true },
    completed: { icon: CheckCircle, color: 'text-green-600 bg-green-100', text: 'Completed' },
    error: { icon: XCircle, color: 'text-red-600 bg-red-100', text: 'Error' },
    waiting: { icon: AlertCircle, color: 'text-orange-600 bg-orange-100', text: 'Waiting' }
  }
  
  const config = configs[status] || configs.idle
  const Icon = config.icon
  const sizeClass = size === 'lg' ? 'h-6 w-6' : size === 'md' ? 'h-5 w-5' : 'h-4 w-4'
  
  return (
    <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
      <Icon className={`${sizeClass} ${config.animate ? 'animate-spin' : ''} ${showText ? 'mr-1' : ''}`} />
      {showText && <span>{config.text}</span>}
    </div>
  )
}

export default StatusIndicator