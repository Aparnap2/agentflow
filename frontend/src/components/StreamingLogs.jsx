import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';

const StreamingLogs = ({ isActive }) => {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('idle');
  const { apiCall } = useAuth();

  useEffect(() => {
    if (!isActive) return;

    const fetchLogs = async () => {
      try {
        const response = await apiCall('/api/agents/logs/live');
        const data = await response.json();
        setLogs(data.logs || []);
        setStatus(data.status || 'idle');
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      }
    };

    // Poll every 2 seconds when active
    const interval = setInterval(fetchLogs, 2000);
    fetchLogs(); // Initial fetch

    return () => clearInterval(interval);
  }, [isActive]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-50';
      case 'completed': return 'text-green-600 bg-green-50';
      case 'error': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getActionIcon = (action) => {
    const icons = {
      'auto_execution_started': '🚀',
      'analyzing_vision': '🧠',
      'task_assignment_complete': '📋',
      'execution_started': '⚡',
      'execution_completed': '✅',
      'auto_execution_completed': '🎉'
    };
    return icons[action] || '📝';
  };

  if (!isActive) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">🤖</div>
        <p>Agent coordination will appear here when active</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🤝 Agent Coordination</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
          {status.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {logs.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            <div className="animate-spin text-2xl mb-2">⚡</div>
            <p>Agents are coordinating...</p>
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="text-xl">{getActionIcon(log.action)}</div>
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-blue-600">{log.agent}</span>
                  <span className="text-gray-500">•</span>
                  <span className="text-sm text-gray-600">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-gray-800 mt-1">
                  <span className="font-medium">{log.action.replace(/_/g, ' ')}</span>
                  {log.data && Object.keys(log.data).length > 0 && (
                    <div className="text-sm text-gray-600 mt-1">
                      {Object.entries(log.data).slice(0, 2).map(([key, value]) => (
                        <span key={key} className="mr-3">
                          {key}: {typeof value === 'object' ? 'data' : value}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default StreamingLogs;