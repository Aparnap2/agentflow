/**
 * Real-time Monitoring Component - PRD Section 3.4
 * Displays agent activities, task states, and live logs with filtering
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Filter, 
  Search,
  Play,
  Pause,
  RefreshCw,
  Users,
  Monitor,
  Zap,
  MessageSquare,
  Database,
  Globe
} from 'lucide-react';
import apiService from '../services/api';

const AGENT_STATUS_COLORS = {
  'active': 'bg-green-100 text-green-800 border-green-200',
  'thinking': 'bg-blue-100 text-blue-800 border-blue-200',
  'waiting': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'error': 'bg-red-100 text-red-800 border-red-200',
  'idle': 'bg-gray-100 text-gray-800 border-gray-200'
};

const TASK_STATUS_COLORS = {
  'pending': 'bg-gray-100 text-gray-800',
  'in-progress': 'bg-blue-100 text-blue-800',
  'completed': 'bg-green-100 text-green-800',
  'failed': 'bg-red-100 text-red-800'
};

const RealtimeMonitoring = ({ sessionId }) => {
  const [logs, setLogs] = useState([]);
  const [agents, setAgents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({});
  const [filters, setFilters] = useState({
    agent: '',
    task: '',
    timestamp: '',
    logLevel: 'all'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const logsEndRef = useRef(null);

  useEffect(() => {
    // Initialize WebSocket connection for real-time updates
    const initializeMonitoring = async () => {
      try {
        // Connect to WebSocket
        apiService.connectWebSocket();
        
        // Set up event listeners
        apiService.on('websocket:connected', () => {
          setIsConnected(true);
          console.log('🔌 Real-time monitoring connected');
        });
        
        apiService.on('websocket:disconnected', () => {
          setIsConnected(false);
          console.log('🔌 Real-time monitoring disconnected');
        });
        
        // Listen for specific events
        apiService.on('event:agent_status_updated', handleAgentStatusUpdate);
        apiService.on('event:task_started', handleTaskEvent);
        apiService.on('event:task_completed', handleTaskEvent);
        apiService.on('event:task_failed', handleTaskEvent);
        apiService.on('event:context_updated', handleContextUpdate);
        apiService.on('event:log_entry', handleLogEntry);
        
        // Initial data fetch
        await fetchInitialData();
        
      } catch (error) {
        console.error('Failed to initialize monitoring:', error);
      }
    };

    initializeMonitoring();

    // Cleanup on unmount
    return () => {
      apiService.off('websocket:connected');
      apiService.off('websocket:disconnected');
      apiService.off('event:agent_status_updated', handleAgentStatusUpdate);
      apiService.off('event:task_started', handleTaskEvent);
      apiService.off('event:task_completed', handleTaskEvent);
      apiService.off('event:task_failed', handleTaskEvent);
      apiService.off('event:context_updated', handleContextUpdate);
      apiService.off('event:log_entry', handleLogEntry);
    };
  }, [sessionId]);

  useEffect(() => {
    // Auto-refresh data every 5 seconds
    if (autoRefresh) {
      const interval = setInterval(fetchLiveData, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, sessionId]);

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (autoRefresh && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoRefresh]);

  const fetchInitialData = async () => {
    try {
      // Fetch session status and agents
      const sessionStatus = await apiService.getSessionStatus(sessionId);
      if (sessionStatus.agents) {
        setAgents(Object.entries(sessionStatus.agents).map(([name, status]) => ({
          name,
          ...status
        })));
      }
      
      // Fetch live logs
      const liveLogs = await apiService.getLiveLogs(sessionId);
      if (liveLogs.logs) {
        setLogs(liveLogs.logs);
      }
      
      // Fetch system metrics
      const metrics = await apiService.getSystemMetrics();
      setSystemMetrics(metrics);
      
    } catch (error) {
      console.error('Failed to fetch initial monitoring data:', error);
    }
  };

  const fetchLiveData = async () => {
    try {
      const liveLogs = await apiService.getLiveLogs(sessionId);
      if (liveLogs.logs && liveLogs.logs.length > logs.length) {
        setLogs(liveLogs.logs);
      }
    } catch (error) {
      console.error('Failed to fetch live data:', error);
    }
  };

  const handleAgentStatusUpdate = (event) => {
    const { agent_id, status, current_task } = event.data;
    setAgents(prev => prev.map(agent => 
      agent.name === agent_id 
        ? { ...agent, status, current_task }
        : agent
    ));
    
    addLogEntry({
      timestamp: event.timestamp,
      agent: agent_id,
      level: 'info',
      message: `Agent ${agent_id} status: ${status}`,
      type: 'agent_status'
    });
  };

  const handleTaskEvent = (event) => {
    const { task_id, agent_id, status, task_type } = event.data;
    
    addLogEntry({
      timestamp: event.timestamp,
      agent: agent_id,
      level: event.type === 'task_failed' ? 'error' : 'info',
      message: `Task ${task_id} (${task_type}): ${status}`,
      type: event.type
    });
  };

  const handleContextUpdate = (event) => {
    const { update_count, agent_id } = event.data;
    
    addLogEntry({
      timestamp: event.timestamp,
      agent: agent_id || 'System',
      level: 'info',
      message: `Context updated: ${update_count} changes`,
      type: 'context_update'
    });
  };

  const handleLogEntry = (event) => {
    addLogEntry(event.data);
  };

  const addLogEntry = (entry) => {
    setLogs(prev => [...prev, {
      id: Date.now() + Math.random(),
      timestamp: entry.timestamp || new Date().toISOString(),
      agent: entry.agent || 'System',
      level: entry.level || 'info',
      message: entry.message,
      type: entry.type || 'log',
      ...entry
    }]);
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = !searchTerm || 
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.agent.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesAgent = !filters.agent || log.agent === filters.agent;
    const matchesLevel = filters.logLevel === 'all' || log.level === filters.logLevel;
    
    return matchesSearch && matchesAgent && matchesLevel;
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'thinking': return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'waiting': return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-600" />;
      default: return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const getLevelIcon = (level) => {
    switch (level) {
      case 'error': return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'warning': return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case 'info': return <Activity className="h-4 w-4 text-blue-600" />;
      default: return <Monitor className="h-4 w-4 text-gray-600" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Monitor className="h-6 w-6 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Real-time Monitoring</h3>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${
              isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1 rounded-md text-sm font-medium ${
                autoRefresh 
                  ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              }`}
            >
              {autoRefresh ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {autoRefresh ? 'Pause' : 'Resume'}
            </button>
            <button
              onClick={fetchLiveData}
              className="px-3 py-1 bg-blue-100 text-blue-800 hover:bg-blue-200 rounded-md text-sm font-medium"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Agent Status Cards */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Agent Status</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {agents.map((agent) => (
            <div key={agent.name} className={`p-3 rounded-lg border ${AGENT_STATUS_COLORS[agent.status] || AGENT_STATUS_COLORS.idle}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(agent.status)}
                  <span className="font-medium text-sm">{agent.name}</span>
                </div>
                <span className="text-xs">{agent.status}</span>
              </div>
              {agent.current_task && (
                <div className="mt-2 text-xs opacity-75">
                  Task: {agent.current_task}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              value={filters.agent}
              onChange={(e) => setFilters(prev => ({ ...prev, agent: e.target.value }))}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Agents</option>
              {agents.map(agent => (
                <option key={agent.name} value={agent.name}>{agent.name}</option>
              ))}
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <select
              value={filters.logLevel}
              onChange={(e) => setFilters(prev => ({ ...prev, logLevel: e.target.value }))}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>
      </div>

      {/* Live Logs */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Live Logs</h4>
        <div className="h-64 overflow-y-auto bg-gray-50 rounded-md p-3 font-mono text-sm">
          {filteredLogs.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              No logs available. Waiting for agent activity...
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div key={log.id} className="mb-2 p-2 bg-white rounded border border-gray-200">
                <div className="flex items-start gap-2">
                  {getLevelIcon(log.level)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                      <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{log.agent}</span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">{log.level}</span>
                    </div>
                    <div className="text-gray-900">{log.message}</div>
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* System Metrics */}
      {Object.keys(systemMetrics).length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <h4 className="text-sm font-medium text-gray-900 mb-3">System Metrics</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-3 rounded border">
              <div className="text-xs text-gray-500">Active Sessions</div>
              <div className="text-lg font-semibold">{systemMetrics.active_sessions || 0}</div>
            </div>
            <div className="bg-white p-3 rounded border">
              <div className="text-xs text-gray-500">Queue Length</div>
              <div className="text-lg font-semibold">{systemMetrics.queue_length || 0}</div>
            </div>
            <div className="bg-white p-3 rounded border">
              <div className="text-xs text-gray-500">Avg Response Time</div>
              <div className="text-lg font-semibold">{systemMetrics.avg_response_time || 0}ms</div>
            </div>
            <div className="bg-white p-3 rounded border">
              <div className="text-xs text-gray-500">Success Rate</div>
              <div className="text-lg font-semibold">{systemMetrics.success_rate || 0}%</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeMonitoring;