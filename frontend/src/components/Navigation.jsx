import { Link, useLocation } from 'react-router-dom'
import { Brain, Users, FileText, Settings, GitBranch, Clock, Eye, AlertCircle, BarChart3, TrendingUp, Zap, Activity } from 'lucide-react'

const Navigation = ({ pendingApprovalsCount = 0 }) => {
  const location = useLocation()
  
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    { path: '/start', label: 'Start', icon: Brain },
    { path: '/vision', label: 'Vision', icon: Eye },
    { path: '/reports', label: 'Reports', icon: TrendingUp },
    { path: '/analytics', label: 'Analytics', icon: Zap },
    { path: '/office', label: 'Virtual Office', icon: Users },
    { path: '/history', label: 'History', icon: Clock },
    { path: '/monitoring', label: 'Monitoring', icon: Activity },
    { path: '/outputs', label: 'Outputs', icon: FileText },
    { path: '/settings', label: 'Settings', icon: Settings }
  ]
  
  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">AgentFlow</span>
          </div>
          
          <div className="flex items-center space-x-8">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === path || (path === '/dashboard' && location.pathname === '/')
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            ))}
            
            {/* Approval indicator */}
            {pendingApprovalsCount > 0 && (
              <div className="flex items-center space-x-2 px-3 py-2 bg-orange-100 text-orange-800 rounded-md">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {pendingApprovalsCount} Approval{pendingApprovalsCount !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation