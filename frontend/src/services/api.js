/**
 * Enhanced API service with error handling, caching, and retry logic
 */

import axios from 'axios';

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cache for API responses
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle auth errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      localStorage.removeItem('authToken');
      window.location.href = '/login';
      return Promise.reject(error);
    }
    
    // Handle network errors with retry
    if (!error.response && originalRequest._retryCount < MAX_RETRIES) {
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
      
      console.log(`Retrying request (${originalRequest._retryCount}/${MAX_RETRIES}): ${originalRequest.url}`);
      
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * originalRequest._retryCount));
      return api(originalRequest);
    }
    
    return Promise.reject(error);
  }
);

// Cache utilities
const getCacheKey = (url, params) => {
  return `${url}?${new URLSearchParams(params).toString()}`;
};

const getCachedResponse = (key) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  cache.delete(key);
  return null;
};

const setCachedResponse = (key, data) => {
  cache.set(key, {
    data,
    timestamp: Date.now(),
  });
};

// API service class
class APIService {
  constructor() {
    this.websocket = null;
    this.eventListeners = new Map();
  }

  // WebSocket connection
  connectWebSocket() {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/agent-updates';
    this.websocket = new WebSocket(wsUrl);
    
    this.websocket.onopen = () => {
      console.log('WebSocket connected');
      this.emit('websocket:connected');
    };
    
    this.websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit(`websocket:${data.type}`, data);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };
    
    this.websocket.onclose = () => {
      console.log('WebSocket disconnected');
      this.emit('websocket:disconnected');
      
      // Reconnect after 3 seconds
      setTimeout(() => this.connectWebSocket(), 3000);
    };
    
    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('websocket:error', error);
    };
  }

  // Event system
  on(event, listener) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(listener);
  }

  off(event, listener) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    const listeners = this.eventListeners.get(event) || [];
    listeners.forEach(listener => listener(data));
  }

  // Authentication
  async signup(userData) {
    try {
      const response = await api.post('/api/auth/signup', userData);
      if (response.data.access_token) {
        localStorage.setItem('authToken', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Signup failed');
    }
  }

  async signin(credentials) {
    try {
      const response = await api.post('/api/auth/signin', credentials);
      if (response.data.access_token) {
        localStorage.setItem('authToken', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Signin failed');
    }
  }

  async getCurrentUser() {
    try {
      const response = await api.get('/api/auth/user');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get user');
    }
  }

  // Projects
  async getProjects() {
    try {
      const cacheKey = getCacheKey('/api/projects', {});
      const cached = getCachedResponse(cacheKey);
      
      if (cached) {
        return cached;
      }
      
      const response = await api.get('/api/projects');
      setCachedResponse(cacheKey, response.data);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get projects');
    }
  }

  async createProject(projectData) {
    try {
      const response = await api.post('/api/projects', projectData);
      
      // Clear projects cache
      const cacheKey = getCacheKey('/api/projects', {});
      cache.delete(cacheKey);
      
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to create project');
    }
  }

  // Agents
  async getAgentsStatus() {
    try {
      const response = await api.get('/api/agents/status');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get agents status');
    }
  }

  async getAgentsList() {
    try {
      const cacheKey = getCacheKey('/api/agents/list', {});
      const cached = getCachedResponse(cacheKey);
      
      if (cached) {
        return cached;
      }
      
      const response = await api.get('/api/agents/list');
      setCachedResponse(cacheKey, response.data);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get agents list');
    }
  }

  async getAgentPersonalities() {
    try {
      const cacheKey = getCacheKey('/api/agents/personalities', {});
      const cached = getCachedResponse(cacheKey);
      
      if (cached) {
        return cached;
      }
      
      const response = await api.get('/api/agents/personalities');
      setCachedResponse(cacheKey, response.data);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get agent personalities');
    }
  }

  async executeAgent(agentData) {
    try {
      const response = await api.post('/api/agents/execute', agentData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to execute agent');
    }
  }

  // Conversations
  async startConversation(message) {
    try {
      const response = await api.post('/api/conversation/start', { message });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to start conversation');
    }
  }

  async continueConversation(conversationId, message) {
    try {
      const response = await api.post(`/api/conversation/${conversationId}/message`, { message });
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to continue conversation');
    }
  }

  async approveConversation(conversationId) {
    try {
      const response = await api.post(`/api/conversation/${conversationId}/approve`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to approve conversation');
    }
  }

  // Projects execution
  async startProject(projectData) {
    try {
      const response = await api.post('/api/start-project', projectData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to start project');
    }
  }

  async autoExecuteProject(projectData) {
    try {
      const response = await api.post('/api/auto-execute', projectData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to auto-execute project');
    }
  }

  // Outputs and Reports
  async getOutputs() {
    try {
      const response = await api.get('/api/outputs');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get outputs');
    }
  }

  async getComprehensiveReport() {
    try {
      const response = await api.get('/api/reports/comprehensive');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get comprehensive report');
    }
  }

  async getSpecificReport(reportType) {
    try {
      const response = await api.get(`/api/reports/${reportType}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, `Failed to get ${reportType} report`);
    }
  }

  async getDomainReports() {
    try {
      const response = await api.get('/api/reports/domains');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get domain reports');
    }
  }

  async generatePDFReport(reportData) {
    try {
      const response = await api.post('/api/reports/generate-pdf', reportData);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to generate PDF report');
    }
  }

  // Analytics
  async getPredictions() {
    try {
      const response = await api.get('/api/analytics/predictions');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get predictions');
    }
  }

  // Memory
  async getMemoryStats() {
    try {
      const response = await api.get('/api/memory/stats');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get memory stats');
    }
  }

  async getMemoryGraph() {
    try {
      const response = await api.get('/api/memory/graph');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get memory graph');
    }
  }

  async exportMemory() {
    try {
      const response = await api.post('/api/memory/export');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to export memory');
    }
  }

  async clearMemory() {
    try {
      const response = await api.delete('/api/memory/clear');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to clear memory');
    }
  }

  // Timeline
  async getTimeline() {
    try {
      const response = await api.get('/api/timeline');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get timeline');
    }
  }

  // System
  async getHealth() {
    try {
      const response = await api.get('/api/health');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get health status');
    }
  }

  async getAutoExecutionStatus() {
    try {
      const response = await api.get('/api/auto-execute/status');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get auto-execution status');
    }
  }

  async getLiveAgentLogs() {
    try {
      const response = await api.get('/api/agents/logs/live');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to get live agent logs');
    }
  }

  // Testing
  async testCoordination() {
    try {
      const response = await api.post('/api/test-coordination');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Failed to test coordination');
    }
  }

  // Error handling
  handleError(error, defaultMessage = 'An error occurred') {
    console.error('API Error:', error);
    
    if (error.response?.data?.detail) {
      return new Error(error.response.data.detail);
    }
    
    if (error.response?.data?.message) {
      return new Error(error.response.data.message);
    }
    
    if (error.message) {
      return new Error(error.message);
    }
    
    return new Error(defaultMessage);
  }

  // Utility methods
  clearCache() {
    cache.clear();
  }

  getCacheStats() {
    return {
      size: cache.size,
      keys: Array.from(cache.keys()),
    };
  }
}

// Create and export singleton instance
const apiService = new APIService();
export default apiService;

// Export specific methods for convenience
export const {
  signup,
  signin,
  getCurrentUser,
  getProjects,
  createProject,
  getAgentsStatus,
  getAgentsList,
  getAgentPersonalities,
  executeAgent,
  startConversation,
  continueConversation,
  approveConversation,
  startProject,
  autoExecuteProject,
  getOutputs,
  getComprehensiveReport,
  getSpecificReport,
  getDomainReports,
  generatePDFReport,
  getPredictions,
  getMemoryStats,
  getMemoryGraph,
  exportMemory,
  clearMemory,
  getTimeline,
  getHealth,
  getAutoExecutionStatus,
  getLiveAgentLogs,
  testCoordination,
  connectWebSocket,
  on,
  off,
} = apiService;
