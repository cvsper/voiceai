import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiService from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);

  // Check if user is already authenticated on app start
  useEffect(() => {
    const checkAuth = async () => {
      const savedCredentials = localStorage.getItem('voiceai_credentials');
      if (savedCredentials) {
        try {
          const { username, password } = JSON.parse(savedCredentials);
          // Update API service credentials
          (apiService as any).updateCredentials(username, password);
          
          // Test the credentials by making a protected API call
          await apiService.getDashboardMetrics();
          setIsAuthenticated(true);
        } catch (error) {
          // Credentials are invalid, remove them
          localStorage.removeItem('voiceai_credentials');
          setIsAuthenticated(false);
        }
      }
      setInitialLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      // Update API service credentials temporarily
      const tempApiService = { ...apiService };
      (tempApiService as any).updateCredentials?.(username, password);

      // Test the credentials with a protected endpoint
      await apiService.getDashboardMetrics();

      // If successful, save credentials and update state
      localStorage.setItem('voiceai_credentials', JSON.stringify({ username, password }));
      (apiService as any).updateCredentials?.(username, password);
      setIsAuthenticated(true);
      setLoading(false);
      return true;
    } catch (error: any) {
      setError(error.message || 'Invalid credentials');
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('voiceai_credentials');
    setIsAuthenticated(false);
    setError(null);
    // Reset API service credentials
    (apiService as any).updateCredentials?.('', '');
  };

  const value = {
    isAuthenticated,
    login,
    logout,
    loading,
    error
  };

  // Show loading spinner during initial auth check
  if (initialLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};