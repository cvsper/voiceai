import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import CallLogs from './pages/CallLogs';
import LiveMonitor from './pages/LiveMonitor';
import Settings from './pages/Settings';
import LoginForm from './components/LoginForm';

const AppContent: React.FC = () => {
  const { isAuthenticated, login, loading, error } = useAuth();

  if (!isAuthenticated) {
    return <LoginForm onLogin={login} loading={loading} error={error} />;
  }

  return (
    <Router>
      <div className="bg-gray-900 text-white min-h-screen">
        <Routes>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="call-logs" element={<CallLogs />} />
            <Route path="live-monitor" element={<LiveMonitor />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
};

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}