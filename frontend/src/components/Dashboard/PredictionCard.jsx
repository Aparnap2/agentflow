import { TrendingUp, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

const PredictionCard = ({ title, prediction, confidence, recommendations = [] }) => {
  const getConfidenceColor = (level) => {
    switch(level) {
      case 'high': return 'text-green-600 bg-green-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getIcon = () => {
    if (confidence === 'high') return <CheckCircle className="h-5 w-5 text-green-500" />
    if (confidence === 'medium') return <Clock className="h-5 w-5 text-yellow-500" />
    return <AlertTriangle className="h-5 w-5 text-red-500" />
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {getIcon()}
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Prediction</span>
          <span className="font-medium text-gray-900">{prediction}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Confidence</span>
          <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(confidence)}`}>
            {confidence}
          </span>
        </div>
        
        {recommendations.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h4>
            <ul className="space-y-1">
              {recommendations.slice(0, 3).map((rec, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="w-1 h-1 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default PredictionCard