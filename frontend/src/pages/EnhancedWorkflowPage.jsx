import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Send, 
  CheckCircle, 
  ArrowRight, 
  Brain, 
  Activity, 
  Clock,
  AlertCircle,
  Play,
  Monitor,
  MessageSquare,
  Settings,
  BarChart3,
  FileText,
  Eye,
  Zap
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import apiService from '../services/api';

const WORKFLOW_STEPS = {
  CHATTING: 'chatting',
  READY_FOR_APPROVAL: 'ready_for_approval', 
  EXECUTING: 'executing',
  COMPLETED: 'completed',
  ERROR: 'error'
};

const STEP_LABELS = {
  [WORKFLOW_STEPS.CHATTING]: 'Discussing Vision',
  [WORKFLOW_STEPS.READY_FOR_APPROVAL]: 'Ready for Approval',
  [WORKFLOW_STEPS.EXECUTING]: 'Agents Working',
  [WORKFLOW_STEPS.COMPLETED]: 'Completed',
  [WORKFLOW_STEPS.ERROR]: 'Error'
};

const StepIndicator = ({ currentStep, steps }) => {
  const stepOrder = [
    WORKFLOW_STEPS.CHATTING,
    WORKFLOW_STEPS.READY_FOR_APPROVAL,
    WORKFLOW_STEPS.EXECUTING,
    WORKFLOW_STEPS.COMPLETED
  ];

  const getStepIndex = (step) => stepOrder.indexOf(step);
  const currentIndex = getStepIndex(currentStep);

  return (
    <div className="flex items-center justify-between mb-8 px-4">
      {stepOrder.map((step, index) => {
        const isActive = index === currentIndex;
        const isCompleted = index < currentIndex;
        const isError = currentStep === WORKFLOW_STEPS.ERROR;
        
        return (
          <div key={step} className="flex items-center">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
              isError && index === currentIndex 
                ? 'bg-red-100 border-red-500 text-red-600'
                : isCompleted 
                  ? 'bg-green-100 border-green-500 text-green-600'
                  : isActive 
                    ? 'bg-blue-100 border-blue-500 text-blue-600'
                    : 'bg-gray-100 border-gray-300 text-gray-400'
            }`}>
              {isCompleted ? (
                <CheckCircle className="h-5 w-5" />
              ) : isError && index === currentIndex ? (
                <AlertCircle className="h-5 w-5" />
              ) : isActive ? (
                <Activity className="h-5 w-5 animate-pulse" />
              ) : (
                <div className="w-3 h-3 rounded-full bg-current" />
              )}
            </div>
            <div className="ml-2 min-w-0">
              <p className={`text-sm font-medium ${
                isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-400'
              }`}>
                {STEP_LABELS[step]}
              </p>
            </div>
            {index < stepOrder.length - 1 && (
              <div className={`flex-1 h-0.5 mx-4 ${
                index < currentIndex ? 'bg-green-500' : 'bg-gray-200'
              }`} />
            )}
          </div>
        );
      })}
    </div>
  );
};

const ChatInterface = ({ sessionId, onReadyForApproval, initialMessages = [] }) => {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await apiService.continueEnhancedSession(sessionId, input);

      const assistantMessage = { role: 'assistant', content: response.response };
      setMessages(prev => [...prev, assistantMessage]);
      
      if (response.ready_for_approval) {
        onReadyForApproval();
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border flex flex-col h-96">
      <div className="flex-1 p-4 overflow-y-auto">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <Brain className="h-10 w-10 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Continue Your Conversation</h3>
            <p className="text-gray-600">Keep refining your vision with the AI Cofounder</p>
          </div>
        )}

        <div className="space-y-4">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl px-4 py-3 rounded-lg ${
                message.role === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-900'
              }`}>
                {message.role === 'user' ? (
                  <div className="whitespace-pre-wrap">{message.content}</div>
                ) : (
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-gray-600">AI Cofounder is thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t p-4">
        <div className="flex space-x-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Continue discussing your startup idea..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={2}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

const LiveMonitoring = ({ sessionId }) => {
  const [logs, setLogs] = useState([]);
  const [sessionStatus, setSessionStatus] = useState({});
  const [systemMetrics, setSystemMetrics] = useState({});
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
  const logsEndRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket for real-time events
    apiService.connectWebSocket();
    
    const handleWebSocketConnected = () => {
      setIsWebSocketConnected(true);
      console.log('🔌 Connected to real-time agent events');
    };
    
    const handleWebSocketDisconnected = () => {
      setIsWebSocketConnected(false);
      console.log('🔌 Disconnected from real-time agent events');
    };

    const handleTaskEvent = (event) => {
      if (event.data.session_id === sessionId) {
        const logEntry = {
          timestamp: event.timestamp,
          role: 'system',
          content: `🤖 ${event.data.agent_id || 'Agent'}: ${event.type.replace('_', ' ')}`,
          type: event.type,
          data: event.data
        };
        setLogs(prev => [...prev, logEntry]);
      }
    };

    const handleContextBatch = (event) => {
      const logEntry = {
        timestamp: event.timestamp,
        role: 'system',
        content: `📦 Context batch processed: ${event.data.update_count} updates`,
        type: event.type,
        data: event.data
      };
      setLogs(prev => [...prev, logEntry]);
    };

    // Subscribe to real-time events
    apiService.on('websocket:connected', handleWebSocketConnected);
    apiService.on('websocket:disconnected', handleWebSocketDisconnected);
    apiService.on('event:task_processing', handleTaskEvent);
    apiService.on('event:task_completed', handleTaskEvent);
    apiService.on('event:task_failed', handleTaskEvent);
    apiService.on('event:context_batch_processed', handleContextBatch);
    apiService.on('event:session_started', handleTaskEvent);
    apiService.on('event:session_cancelled', handleTaskEvent);

    // Fallback polling when WebSocket is disconnected
    const pollInterval = setInterval(async () => {
      if (!isWebSocketConnected) {
        try {
          const [logsRes, statusRes, metricsRes] = await Promise.all([
            apiService.getLiveLogs(sessionId),
            apiService.getSessionStatus(sessionId),
            apiService.getSystemMetrics()
          ]);
          
          setLogs(logsRes || []);
          setSessionStatus(statusRes || {});
          setSystemMetrics(metricsRes || {});
        } catch (error) {
          console.error('Failed to fetch monitoring data:', error);
        }
      }
    }, 3000);

    // Initial data fetch
    const fetchInitialData = async () => {
      try {
        const [statusRes, metricsRes] = await Promise.all([
          apiService.getSessionStatus(sessionId),
          apiService.getSystemMetrics()
        ]);
        
        setSessionStatus(statusRes || {});
        setSystemMetrics(metricsRes || {});
      } catch (error) {
        console.error('Failed to fetch initial monitoring data:', error);
      }
    };

    fetchInitialData();

    return () => {
      clearInterval(pollInterval);
      apiService.off('websocket:connected', handleWebSocketConnected);
      apiService.off('websocket:disconnected', handleWebSocketDisconnected);
      apiService.off('event:task_processing', handleTaskEvent);
      apiService.off('event:task_completed', handleTaskEvent);
      apiService.off('event:task_failed', handleTaskEvent);
      apiService.off('event:context_batch_processed', handleContextBatch);
      apiService.off('event:session_started', handleTaskEvent);
      apiService.off('event:session_cancelled', handleTaskEvent);
    };
  }, [sessionId, isWebSocketConnected]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Live Logs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="border-b p-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Activity className={`h-5 w-5 mr-2 ${isWebSocketConnected ? 'text-green-500' : 'text-yellow-500'}`} />
            Live Agent Activity
            <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
              isWebSocketConnected 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {isWebSocketConnected ? 'Live' : 'Polling'}
            </span>
          </h3>
        </div>
        <div className="p-4 h-80 overflow-y-auto bg-gray-50">
          {logs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              Waiting for agent activity...
            </div>
          ) : (
            <div className="space-y-2">
              {logs.map((log, index) => (
                <div key={index} className="text-sm">
                  <span className="text-gray-500 font-mono">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`ml-2 ${
                    log.role === 'system' ? 'text-blue-600' : 
                    log.role === 'user' ? 'text-green-600' : 'text-gray-800'
                  }`}>
                    {log.content}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Agent Status */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="border-b p-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Monitor className="h-5 w-5 mr-2 text-blue-500" />
            Agent Status
          </h3>
        </div>
        <div className="p-4">
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Session Status:</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                sessionStatus.status === 'executing' ? 'bg-blue-100 text-blue-800' :
                sessionStatus.status === 'completed' ? 'bg-green-100 text-green-800' :
                sessionStatus.status === 'chatting' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {sessionStatus.status || 'Unknown'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Results Generated:</span>
              <span className="font-semibold">{sessionStatus.results_count || 0}</span>
            </div>

            {sessionStatus.agent_tasks && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Agent Tasks:</h4>
                {Object.entries(sessionStatus.agent_tasks).map(([agent, status]) => (
                  <div key={agent} className="flex justify-between text-sm">
                    <span className="text-gray-600">{agent}:</span>
                    <span className={`px-1 rounded text-xs ${
                      status === 'completed' ? 'bg-green-100 text-green-800' :
                      status === 'processing' ? 'bg-blue-100 text-blue-800' :
                      status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Metrics */}
      <div className="bg-white rounded-lg shadow-sm border lg:col-span-2">
        <div className="border-b p-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-purple-500" />
            System Metrics
          </h3>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {systemMetrics.active_sessions || 0}
              </div>
              <div className="text-sm text-gray-600">Active Sessions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {systemMetrics.completed_sessions || 0}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {systemMetrics.queue_metrics?.tasks_processed || 0}
              </div>
              <div className="text-sm text-gray-600">Tasks Processed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {systemMetrics.live_logs_count || 0}
              </div>
              <div className="text-sm text-gray-600">Live Logs</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const EnhancedWorkflowPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(WORKFLOW_STEPS.CHATTING);
  const [sessionId, setSessionId] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialMessages, setInitialMessages] = useState([]);

  useEffect(() => {
    if (location.state) {
      setSessionId(location.state.sessionId);
      setConversationId(location.state.conversationId);
      
      // Set up initial messages if provided
      const messages = [];
      if (location.state.initialUserMessage) {
        messages.push({ role: 'user', content: location.state.initialUserMessage });
      }
      if (location.state.initialAssistantMessage) {
        messages.push({ role: 'assistant', content: location.state.initialAssistantMessage });
      }
      setInitialMessages(messages);
    } else {
      // Handle case where user navigated directly
      navigate('/');
    }
  }, [location.state, navigate]);

  const handleReadyForApproval = () => {
    setCurrentStep(WORKFLOW_STEPS.READY_FOR_APPROVAL);
  };

  const handleApproveAndExecute = async () => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await apiService.approveAndExecute(sessionId);
      setCurrentStep(WORKFLOW_STEPS.EXECUTING);
      
      // Start monitoring the execution
      const monitorInterval = setInterval(async () => {
        try {
          const statusRes = await apiService.getSessionStatus(sessionId);
          if (statusRes.status === 'completed') {
            setCurrentStep(WORKFLOW_STEPS.COMPLETED);
            clearInterval(monitorInterval);
          } else if (statusRes.status === 'error' || statusRes.status === 'failed') {
            setCurrentStep(WORKFLOW_STEPS.ERROR);
            clearInterval(monitorInterval);
          }
        } catch (err) {
          console.error('Failed to check status:', err);
        }
      }, 3000);

      // Clean up after 5 minutes max
      setTimeout(() => clearInterval(monitorInterval), 300000);
      
    } catch (err) {
      console.error('Failed to approve and execute:', err);
      setError(`Failed to start execution: ${err.message}`);
      setCurrentStep(WORKFLOW_STEPS.ERROR);
    } finally {
      setLoading(false);
    }
  };

  const handleViewResults = () => {
    navigate('/enhanced-results', { state: { sessionId } });
  };

  if (!sessionId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Session Not Found</h2>
          <p className="text-gray-600">Please start a new enhanced workflow session.</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <Zap className="h-6 w-6 mr-2 text-blue-600" />
                Enhanced AgentFlow Workflow
              </h1>
              <p className="text-gray-600 mt-1">
                AI-powered project development from vision to execution
              </p>
            </div>
            <div className="text-sm text-gray-500">
              Session: {sessionId?.slice(0, 8)}...
            </div>
          </div>
        </div>

        {/* Step Indicator */}
        <StepIndicator currentStep={currentStep} />

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

        {/* Main Content */}
        <div className="space-y-8">
          {/* Chat Phase */}
          {currentStep === WORKFLOW_STEPS.CHATTING && (
            <div>
              <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2 text-blue-600" />
                  Discuss Your Vision with AI Cofounder
                </h2>
                <ChatInterface 
                  sessionId={sessionId} 
                  onReadyForApproval={handleReadyForApproval}
                  initialMessages={initialMessages}
                />
              </div>
            </div>
          )}

          {/* Approval Phase */}
          {currentStep === WORKFLOW_STEPS.READY_FOR_APPROVAL && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Vision Ready for Approval
                </h2>
                <p className="text-gray-600 mb-6">
                  Your AI Cofounder has prepared a comprehensive plan. Ready to unleash the specialist agents?
                </p>
                <button
                  onClick={handleApproveAndExecute}
                  disabled={loading}
                  className="flex items-center mx-auto px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  ) : (
                    <Play className="h-5 w-5 mr-2" />
                  )}
                  Approve & Start Execution
                </button>
              </div>
            </div>
          )}

          {/* Execution Phase */}
          {(currentStep === WORKFLOW_STEPS.EXECUTING || currentStep === WORKFLOW_STEPS.COMPLETED) && (
            <div>
              <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                  <Monitor className="h-5 w-5 mr-2 text-blue-600" />
                  Real-time Agent Execution
                </h2>
                {currentStep === WORKFLOW_STEPS.EXECUTING && (
                  <p className="text-gray-600 mb-4">
                    Watch your specialist agents work together to bring your vision to life.
                  </p>
                )}
                {currentStep === WORKFLOW_STEPS.COMPLETED && (
                  <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                        <span className="text-green-800 font-medium">Execution Completed!</span>
                      </div>
                      <button
                        onClick={handleViewResults}
                        className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        View Results
                      </button>
                    </div>
                  </div>
                )}
              </div>
              
              <LiveMonitoring sessionId={sessionId} />
            </div>
          )}

          {/* Error State */}
          {currentStep === WORKFLOW_STEPS.ERROR && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="text-center">
                <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Execution Error
                </h2>
                <p className="text-gray-600 mb-6">
                  Something went wrong during execution. Please check the logs or try again.
                </p>
                <div className="flex justify-center space-x-4">
                  <button
                    onClick={() => setCurrentStep(WORKFLOW_STEPS.READY_FOR_APPROVAL)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Try Again
                  </button>
                  <button
                    onClick={() => navigate('/')}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Start New Session
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedWorkflowPage;
