import React from 'react';
import { AuthProvider, useAuth } from './components/AuthProvider';
import AuthScreen from './components/AuthScreen';
import Dashboard from './components/Dashboard';

const AppContent = () => {
  const { user, loading } = useAuth();

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

  return user ? <Dashboard /> : <AuthScreen />;
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;