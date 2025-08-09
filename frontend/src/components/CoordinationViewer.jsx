import React, { useState, useEffect } from 'react';

const CoordinationViewer = () => {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('idle');
  const [isRunning, setIsRunning] = useState(false);

  // Poll for logs every 2 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/agents/logs/live');
        const data = await response.json();
        setLogs(data.logs || []);
        setStatus(data.status || 'idle');
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const startTestCoordination = async () => {
    setIsRunning(true);
    try {
      const response = await fetch('/api/test-coordination', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      console.log('Coordination started:', result);
    } catch (error) {
      console.error('Failed to start coordination:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'auto_execution_started': return '🚀';
      case 'analyzing_vision': return '🧠';
      case 'task_assignment_complete': return '📋';
      case 'execution_started': return '⚡';
      case 'execution_completed': return '✅';
      case 'auto_execution_completed': return '🎉';
      default: return '📝';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                🤝 Agent Coordination Center
              </h2>
              <p className="text-gray-600 mt-1">
                Watch AI agents coordinate and communicate in real-time
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`font-semibold ${getStatusColor(status)}`}>
                Status: {status.toUpperCase()}
              </div>
              <button
                onClick={startTestCoordination}
                disabled={isRunning || status === 'running'}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {status === 'running' ? 'Running...' : 'Start Test Coordination'}
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            📊 Live Execution Logs ({logs.length} entries)
          </h3>
          
          {logs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🤖</div>
              <p>No coordination activity yet. Click "Start Test Coordination" to see agents in action!</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="text-2xl">
                    {getActionIcon(log.action)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-blue-600">
                        {log.agent}
                      </span>
                      <span className="text-gray-500">•</span>
                      <span className="text-sm text-gray-600">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-gray-800 mt-1">
                      <span className="font-medium">{log.action.replace(/_/g, ' ')}</span>
                      {log.data && Object.keys(log.data).length > 0 && (
                        <div className="text-sm text-gray-600 mt-1">
                          {Object.entries(log.data).map(([key, value]) => (
                            <span key={key} className="mr-3">
                              {key}: {typeof value === 'object' ? JSON.stringify(value).slice(0, 50) + '...' : value}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 border-t bg-gray-50">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl">🧠</div>
              <div className="text-sm font-medium">Manager</div>
              <div className="text-xs text-gray-600">Auto-assigns tasks</div>
            </div>
            <div>
              <div className="text-2xl">🎯</div>
              <div className="text-sm font-medium">Product</div>
              <div className="text-xs text-gray-600">Defines MVP & users</div>
            </div>
            <div>
              <div className="text-2xl">💰</div>
              <div className="text-sm font-medium">Finance</div>
              <div className="text-xs text-gray-600">Creates projections</div>
            </div>
            <div>
              <div className="text-2xl">📈</div>
              <div className="text-sm font-medium">Marketing</div>
              <div className="text-xs text-gray-600">Plans campaigns</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoordinationViewer;