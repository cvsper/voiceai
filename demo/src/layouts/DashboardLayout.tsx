import React, { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { HomeIcon, PhoneIcon, RadioIcon, SettingsIcon, MenuIcon, XIcon, BellIcon, UserIcon, LogOutIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const DashboardLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { logout } = useAuth();
  
  const navItems = [
    {
      name: 'Dashboard',
      path: '/',
      icon: HomeIcon
    },
    {
      name: 'Call Logs',
      path: '/call-logs',
      icon: PhoneIcon
    },
    {
      name: 'Live Monitor',
      path: '/live-monitor',
      icon: RadioIcon
    },
    {
      name: 'Settings',
      path: '/settings',
      icon: SettingsIcon
    }
  ];

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black/50 lg:hidden" 
          onClick={() => setSidebarOpen(false)} 
        />
      )}
      
      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-30 w-64 transform bg-gray-800 transition duration-200 ease-in-out lg:static lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex h-16 items-center justify-center border-b border-gray-700">
          <h1 className="text-xl font-bold text-white">
            Voice<span className="text-blue-600">AI</span> Dashboard
          </h1>
        </div>
        
        <nav className="mt-5 px-2">
          {navItems.map(item => (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 mt-1 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon className="mr-3 h-5 w-5" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>
        
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
          <button 
            onClick={handleLogout}
            className="flex w-full items-center justify-center rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 mb-2"
          >
            <LogOutIcon className="mr-2 h-4 w-4" />
            Logout
          </button>
          <button className="flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            Test Call
          </button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-gray-800 shadow">
          <div className="flex h-16 items-center justify-between px-4">
            <button
              className="text-gray-400 hover:text-white focus:outline-none lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <MenuIcon className="h-6 w-6" />
            </button>
            
            <div className="flex items-center space-x-4">
              <button className="text-gray-400 hover:text-white focus:outline-none">
                <BellIcon className="h-6 w-6" />
              </button>
              
              <div className="flex items-center">
                <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                </div>
                <span className="ml-2 text-sm font-medium text-gray-300">
                  Admin
                </span>
                <button
                  onClick={handleLogout}
                  className="ml-3 text-gray-400 hover:text-white focus:outline-none"
                  title="Logout"
                >
                  <LogOutIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </header>
        
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto bg-gray-900 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;