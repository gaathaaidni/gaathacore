import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);

  // On mount, you could fetch the current session status from Flask
  useEffect(() => {
    const savedUser = localStorage.getItem('gaatha_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (err) {
        console.error('Failed to parse saved user from localStorage', err);
        localStorage.removeItem('gaatha_user');
      }
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('gaatha_user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    setNotifications([]);
    localStorage.removeItem('gaatha_user');
    localStorage.removeItem('token');
    // Also trigger backend logout
    fetch('/auth/logout');
  };

  const removeNotification = (index) => {
    setNotifications((prev) => prev.filter((_, idx) => idx !== index));
  };

  const clearNotifications = () => setNotifications([]);

  // Centralized fetch wrapper to handle session expiration globally
  const authFetch = async (url, options = {}) => {
    try {
      const token = localStorage.getItem('token');
      
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, { ...options, headers });
      
      if (response.status === 401) {
        logout();
        window.location.href = '/auth/login?expired=true';
        return new Response(JSON.stringify({ detail: 'Unauthorized' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return response;
    } catch (err) {
      throw err;
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, loading, authFetch, notifications, removeNotification, clearNotifications }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);