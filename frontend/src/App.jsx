import React, { useState } from 'react';
import { AuthProvider, useAuth } from './components/AuthProvider';
import AuthScreen from './components/AuthScreen';
import ChatOnboarding from './components/ChatOnboarding';
import { MainDashboard } from './components/dashboard/MainDashboard';
import { Button } from './components/ui/button';
import { BarChart3, MessageSquare } from 'lucide-react';

const AppContent = () => {
  const { user, loading } = useAuth();
  const [currentView, setCurrentView] = useState('chat'); // 'chat' or 'dashboard'

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">🚀</div>
          <p className="text-gray-600">Loading AgentFlow...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthScreen />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-gray-900">AgentFlow</h1>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant={currentView === 'chat' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentView('chat')}
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Chat Interface
              </Button>
              <Button
                variant={currentView === 'dashboard' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentView('dashboard')}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {currentView === 'chat' ? <ChatOnboarding /> : <MainDashboard />}
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;