/**
 * Enhanced Dashboard with real-time agent monitoring and execution
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Users, 
  Activity, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  TrendingUp,
  MessageSquare,
  FileText,
  Settings,
  Filter,
  Search,
  Download
} from 'lucide-react';
import apiService from '../services/api';

const AGENT_CATEGORIES = {
  strategic: { 
    label: 'Strategic', 
    color: 'bg-purple-100 text-purple-800',
    agents: ['Cofounder', 'Manager']
  },
  business: { 
    label: 'Business', 
    color: 'bg-blue-100 text-blue-800',
    agents: ['Product', 'Finance', 'Marketing', 'Legal']
  },
  operations: { 
    label: 'Operations', 
    color: 'bg-green-100 text-green-800',
    agents: ['Sales', 'Operations', 'Workflow', 'Assistant']
  },
  specialized: { 
    label: 'Specialized', 
    color: 'bg-orange-100 text-orange-800',
    agents: ['Closer', 'Amplifier', 'Money']
  }
};

const AgentCard = ({ agent, status, onExecute, onViewDetails }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': case 'completed': return 'text-green-600 bg-green-100';
      case 'working': case 'thinking': return 'text-blue-600 bg-blue-100';
      case 'waiting_approval': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': case 'completed': return <CheckCircle2 className="h-4 w-4" />;
      case 'working': case 'thinking': return <RefreshCw className="h-4 w-4 animate-spin" />;
      case 'waiting_approval': return <Clock className="h-4 w-4" />;
      case 'error': return <AlertCircle className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{agent.name}</h3>
          <p className="text-sm text-gray-600 mt-1">{agent.description}</p>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(status?.status)}`}>
          {getStatusIcon(status?.status)}
          {status?.status || 'idle'}
        </div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600">
          <Users className="h-4 w-4 mr-2" />
          {agent.expertise?.slice(0, 2).join(', ') || 'General AI Agent'}
        </div>
        {status?.current_task && (
          <div className="flex items-center text-sm text-blue-600">
            <Activity className="h-4 w-4 mr-2" />
            Current Task: {status.current_task}
          </div>
        )}
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={() => onExecute(agent.name)}
          className="flex-1 bg-blue-600 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-1"
        >
          <Play className="h-3 w-3" />
          Execute
        </button>
        <button
          onClick={() => onViewDetails(agent)}
          className="px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Details
        </button>
      </div>
    </div>
  );
};

const CategoryFilter = ({ categories, selectedCategory, onCategoryChange }) => (
  <div className="flex flex-wrap gap-2 mb-6">
    <button
      onClick={() => onCategoryChange('all')}
      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
        selectedCategory === 'all' 
          ? 'bg-gray-900 text-white' 
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      All Agents
    </button>
    {Object.entries(categories).map(([key, category]) => (
      <button
        key={key}
        onClick={() => onCategoryChange(key)}
        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
          selectedCategory === key 
            ? category.color 
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        {category.label} ({category.agents.length})
      </button>
    ))}
  </div>
);

const StatsCard = ({ title, value, icon: Icon, color = "blue", trend = null }) => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className={`text-2xl font-bold text-${color}-600 mt-1`}>{value}</p>
        {trend && (
          <div className="flex items-center mt-2 text-sm text-green-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            {trend}
          </div>
        )}
      </div>
      <div className={`p-3 rounded-full bg-${color}-100`}>
        <Icon className={`h-6 w-6 text-${color}-600`} />
      </div>
    </div>
  </div>
);

import { useNavigate } from 'react-router-dom';

const EnhancedDashboard = () => {
  const [agents, setAgents] = useState({});
  const [agentsStatus, setAgentsStatus] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [systemStats, setSystemStats] = useState({});
  const [selectedAgent, setSelectedAgent] = useState(null);
const [activeSession, setActiveSession] = useState(null);
  const navigate = useNavigate();

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      loadAgentsStatus();
      loadSystemStats();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // WebSocket connection
  useEffect(() => {
    apiService.connectWebSocket();
    
    const handleAgentStatus = (data) => {
      setAgentsStatus(prev => ({ ...prev, ...data.data }));
    };
    
    apiService.on('websocket:agent_status', handleAgentStatus);
    
    return () => {
      apiService.off('websocket:agent_status', handleAgentStatus);
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadAgents(),
        loadAgentsStatus(),
        loadSystemStats()
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const data = await apiService.getAgentsList();
      setAgents(data.agents || {});
    } catch (err) {
      console.error('Failed to load agents:', err);
    }
  };

  const loadAgentsStatus = async () => {
    try {
      const data = await apiService.getAgentsStatus();
      setAgentsStatus(data || {});
    } catch (err) {
      console.error('Failed to load agents status:', err);
    }
  };

  const loadSystemStats = async () => {
    try {
      const [health, timeline] = await Promise.all([
        apiService.getHealth(),
        apiService.getTimeline()
      ]);
      
      setSystemStats({
        health,
        totalTasks: timeline?.length || 0,
        completedTasks: timeline?.filter(t => t.status === 'completed').length || 0,
        activeTasks: timeline?.filter(t => t.status === 'active').length || 0
      });
    } catch (err) {
      console.error('Failed to load system stats:', err);
    }
  };

  const handleExecuteAgent = async (agentName) => {
    try {
      const task = `Execute ${agentName} agent with current project context`;
      await apiService.executeAgent({ agent: agentName, task });
      
      // Refresh status after execution
      setTimeout(() => loadAgentsStatus(), 1000);
    } catch (err) {
      console.error('Failed to execute agent:', err);
      setError(`Failed to execute ${agentName}: ${err.message}`);
    }
  };

  const handleStartEnhancedSession = async () => {
    try {
      const message = "I want to start a new business. Can you help me develop a comprehensive business plan?";
      const response = await apiService.startEnhancedSession({
        user_id: 'default_user',
        message: message
      });
      
      setActiveSession(response.session_id);
      
      // Navigate to enhanced workflow page with initial AI response
      navigate('/enhanced-workflow', { 
        state: { 
          sessionId: response.session_id,
          conversationId: response.conversation_id,
          initialAssistantMessage: response.response,
          initialUserMessage: message
        } 
      });
    } catch (err) {
      console.error('Failed to start enhanced session:', err);
      setError(`Failed to start enhanced session: ${err.message}`);
    }
  };

  const handleAutoExecute = async () => {
    try {
      const vision = "AI-powered productivity platform for remote teams with advanced task management and collaboration features";
      await apiService.autoExecuteProject({ vision });
      
      // Start monitoring auto-execution
      setAutoRefresh(true);
    } catch (err) {
      console.error('Failed to auto-execute:', err);
      setError(`Failed to auto-execute: ${err.message}`);
    }
  };

  // Filter agents based on category and search
  const filteredAgents = Object.entries(agents).filter(([name, agent]) => {
    const matchesCategory = selectedCategory === 'all' || 
      AGENT_CATEGORIES[selectedCategory]?.agents.includes(name);
    
    const matchesSearch = !searchTerm || 
      name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesCategory && matchesSearch;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AgentFlow Dashboard</h1>
              <p className="text-gray-600 mt-1">Monitor and control your AI agents</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  autoRefresh 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                <RefreshCw className={`h-4 w-4 mr-1 inline ${autoRefresh ? 'animate-spin' : ''}`} />
                Auto-refresh
              </button>
              <button
                onClick={loadDashboardData}
                className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="h-4 w-4 mr-1 inline" />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5" />
              <div>
                <p className="text-red-800">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="text-red-600 hover:text-red-800 text-sm mt-1"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleStartEnhancedSession}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              <MessageSquare className="h-4 w-4" />
              Start Enhanced Project
            </button>
            <button
              onClick={handleAutoExecute}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <Play className="h-4 w-4" />
              Auto-Execute Demo
            </button>
            <button
              onClick={() => window.open('/outputs', '_blank')}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              <FileText className="h-4 w-4" />
              View Reports
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Agents"
            value={Object.keys(agents).length}
            icon={Users}
            color="blue"
          />
          <StatsCard
            title="Active Agents"
            value={Object.values(agentsStatus).filter(s => s?.status === 'active').length}
            icon={Activity}
            color="green"
            trend="+12% from last hour"
          />
          <StatsCard
            title="Completed Tasks"
            value={systemStats.completedTasks || 0}
            icon={CheckCircle2}
            color="purple"
          />
          <StatsCard
            title="System Health"
            value={systemStats.health?.status === 'healthy' ? '100%' : '85%'}
            icon={TrendingUp}
            color="emerald"
          />
        </div>

        {/* Search and Filter */}
        <div className="mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="relative flex-1 max-w-md">
              <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Search agents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
              <Filter className="h-4 w-4" />
              Filters
            </button>
          </div>
          
          <CategoryFilter
            categories={AGENT_CATEGORIES}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
          />
        </div>

        {/* Agents Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map(([name, agent]) => (
            <AgentCard
              key={name}
              agent={{ ...agent, name }}
              status={agentsStatus[name]}
              onExecute={handleExecuteAgent}
              onViewDetails={setSelectedAgent}
            />
          ))}
        </div>

        {filteredAgents.length === 0 && (
          <div className="text-center py-12">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No agents found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedDashboard;
