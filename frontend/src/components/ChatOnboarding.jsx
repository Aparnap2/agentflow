/**
 * Chat-based Onboarding Component - PRD Section 3.1
 * Main entry point for user interactions with Cofounder Agent
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Brain, CheckCircle, ArrowRight, Sparkles, User, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import apiService from '../services/api';
import { useAuth } from './AuthProvider';

const ChatOnboarding = () => {
  const { user, signOut } = useAuth();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hi! I'm your AI Cofounder. I'll help you define your project vision and create a comprehensive plan. What's your startup idea?",
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [readyForApproval, setReadyForApproval] = useState(false);
  const [projectPlan, setProjectPlan] = useState(null);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { 
      role: 'user', 
      content: input,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      let data;
      if (!sessionId) {
        // Start new session - PRD Section 3.1.1
        data = await apiService.startEnhancedSession({
          user_id: user?.id || 'user_' + Date.now(),
          message: input
        });
        setSessionId(data.session_id);
        
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
        
        // Check if ready for approval
        if (data.ready_for_approval) {
          setReadyForApproval(true);
          setProjectPlan(data.project_plan);
        }
      } else {
        // Continue session - PRD Section 3.1.2
        data = await apiService.continueEnhancedSession(sessionId, input);
        
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
        
        // Check if ready for approval
        if (data.ready_for_approval) {
          setReadyForApproval(true);
          setProjectPlan(data.project_plan);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const approveAndExecute = async () => {
    if (!sessionId) return;

    setLoading(true);
    try {
      // Extract vision from messages
      const visionText = messages
        .filter(m => m.role === 'user')
        .map(m => m.content)
        .join(' ');
      
      // Execute real workflow
      const response = await fetch('http://localhost:8000/api/workflow/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          vision: visionText,
          user_id: user?.id || 'demo_user'
        })
      });
      
      const data = await response.json();
      
      // Navigate to workflow monitoring with real execution data
      navigate('/enhanced-workflow', { 
        state: { 
          sessionId: sessionId,
          projectPlan: projectPlan,
          executionStarted: true,
          workflowData: data
        } 
      });
    } catch (error) {
      console.error('Failed to approve and execute:', error);
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white rounded-xl shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="h-8 w-8" />
              <div>
                <h1 className="text-2xl font-bold">AgentFlow - AI Cofounder</h1>
                <p className="text-blue-100">Chat-based Project Planning & Execution</p>
              </div>
            </div>
            
            {/* User Profile */}
            <div className="flex items-center gap-3">
              {user?.avatar ? (
                <img src={user.avatar} alt={user.name} className="h-8 w-8 rounded-full" />
              ) : (
                <User className="h-8 w-8 p-1 bg-blue-500 rounded-full" />
              )}
              <div className="text-right">
                <p className="text-sm font-medium">{user?.name || 'User'}</p>
                <p className="text-xs text-blue-100">{user?.email}</p>
              </div>
              <button
                onClick={signOut}
                className="p-1 hover:bg-blue-500 rounded transition-colors"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="h-96 overflow-y-auto p-6 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-600">AI Cofounder</span>
                  </div>
                )}
                <ReactMarkdown components={{
                  p: ({node, ...props}) => <p className="prose prose-sm max-w-none" {...props} />
                }}>
                  {message.content}
                </ReactMarkdown>
                <div className="text-xs opacity-70 mt-1">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-sm text-gray-600">AI Cofounder is thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Project Plan Preview */}
        {projectPlan && (
          <div className="border-t border-gray-200 p-6 bg-yellow-50">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-5 w-5 text-yellow-600" />
              <h3 className="font-semibold text-yellow-800">Project Plan Generated</h3>
            </div>
            <div className="bg-white rounded-lg p-4 text-sm">
              <pre className="whitespace-pre-wrap text-gray-700">
                {JSON.stringify(projectPlan, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-gray-200 p-6">
          <div className="flex gap-4">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Describe your startup idea or ask questions..."
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="2"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="h-4 w-4" />
              Send
            </button>
          </div>
          
          {readyForApproval && (
            <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-green-800 font-medium">
                    Project plan is ready for approval
                  </span>
                </div>
                <button
                  onClick={approveAndExecute}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                >
                  <ArrowRight className="h-4 w-4" />
                  Approve & Execute
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatOnboarding;