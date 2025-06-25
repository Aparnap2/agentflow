import { Link, useLocation } from 'react-router-dom'
import { Brain, Users, FileText, Settings } from 'lucide-react'

const Navigation = () => {
  const location = useLocation()
  
  const navItems = [
    { path: '/start', label: 'Start', icon: Brain },
    { path: '/vision', label: 'Vision', icon: Brain },
    { path: '/agents', label: 'Agents', icon: Users },
    { path: '/outputs', label: 'Outputs', icon: FileText }
  ]
  
  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">AgentFlow</span>
          </div>
          
          <div className="flex space-x-8">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === path
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation