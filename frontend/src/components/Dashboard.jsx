import React, { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import StreamingLogs from './StreamingLogs';

const Dashboard = () => {
  const { user, signOut, apiCall } = useAuth();
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [coordinationActive, setCoordinationActive] = useState(false);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await apiCall('/api/projects');
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const startConversation = async () => {
    if (!message.trim()) return;

    setLoading(true);
    try {
      const response = await apiCall('/api/conversation/start', {
        method: 'POST',
        body: JSON.stringify({ message })
      });

      if (response.ok) {
        const data = await response.json();
        setConversation([
          { role: 'user', content: message },
          { role: 'assistant', content: data.response }
        ]);
        setConversationId(data.conversation_id);
        setMessage('');
      } else {
        alert('Failed to start conversation');
      }
    } catch (error) {
      alert('Error starting conversation');
    } finally {
      setLoading(false);
    }
  };

  const approveAndExecute = async () => {
    if (!conversationId) return;

    setLoading(true);
    setCoordinationActive(true);
    
    try {
      const response = await apiCall(`/api/conversation/${conversationId}/approve`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Project ${data.project_id} started! Watch agents coordinate below.`);
        loadProjects(); // Refresh projects
      } else {
        alert('Failed to approve conversation');
        setCoordinationActive(false);
      }
    } catch (error) {
      alert('Error approving conversation');
      setCoordinationActive(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">🚀 AgentFlow</h1>
              <span className="ml-3 text-sm text-gray-500">AI Virtual Office</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Welcome, {user.name || user.email}</span>
              <button
                onClick={signOut}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Conversation Panel */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">💬 AI Cofounder Chat</h2>
            
            {conversation.length === 0 ? (
              <div className="space-y-4">
                <p className="text-gray-600">Start a conversation about your startup idea:</p>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="I want to build a..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) => e.key === 'Enter' && startConversation()}
                  />
                  <button
                    onClick={startConversation}
                    disabled={loading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? '...' : 'Start'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {conversation.map((msg, index) => (
                  <div key={index} className={`p-3 rounded-lg ${
                    msg.role === 'user' ? 'bg-blue-50 ml-8' : 'bg-gray-50 mr-8'
                  }`}>
                    <div className="font-medium text-sm mb-1">
                      {msg.role === 'user' ? 'You' : '🎯 AI Cofounder'}
                    </div>
                    <div className="text-gray-800 whitespace-pre-wrap">{msg.content}</div>
                  </div>
                ))}
                
                {conversationId && !coordinationActive && (
                  <div className="text-center pt-4">
                    <button
                      onClick={approveAndExecute}
                      disabled={loading}
                      className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {loading ? 'Starting...' : '✅ Approve & Start Agent Coordination'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Agent Coordination Panel */}
          <div className="bg-white rounded-lg shadow p-6">
            <StreamingLogs isActive={coordinationActive} />
          </div>
        </div>

        {/* Projects Section */}
        {projects.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">📊 Your Projects</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <div key={project.id} className="border rounded-lg p-4">
                  <h3 className="font-medium">{project.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{project.status}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(project.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;