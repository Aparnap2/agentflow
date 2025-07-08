import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          const response = await fetch('/api/auth/user', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            localStorage.removeItem('auth_token');
          }
        }
      } catch (error) {
        localStorage.removeItem('auth_token');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const signIn = async (email, password) => {
    try {
      const response = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (data.success && data.user) {
        setUser(data.user);
        localStorage.setItem('auth_token', data.access_token);
        return { success: true };
      } else {
        return { success: false, error: data.error || 'Sign in failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const signUp = async (email, password, name) => {
    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name })
      });
      
      const data = await response.json();
      
      if (data.success && data.user) {
        setUser(data.user);
        localStorage.setItem('auth_token', data.access_token);
        return { success: true };
      } else {
        return { success: false, error: data.error || 'Sign up failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const signOut = () => {
    setUser(null);
    localStorage.removeItem('auth_token');
  };

  // Helper function to make authenticated API calls
  const apiCall = async (url, options = {}) => {
    const token = localStorage.getItem('auth_token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    };
    
    return fetch(url, { ...options, headers });
  };

  const value = {
    user,
    loading,
    signIn,
    signUp,
    signOut,
    apiCall
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};