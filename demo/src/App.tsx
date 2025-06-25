import React, { useState } from 'react';
import { Header } from './components/Header';
import { LandingPage } from './components/LandingPage';
import { IntakeForm } from './components/IntakeForm';
import { AdminDashboard } from './components/AdminDashboard';
import { VoiceAIDashboard } from './components/VoiceAIDashboard';
export function App() {
  const [currentPage, setCurrentPage] = useState('voiceai');
  const [language, setLanguage] = useState('en'); // 'en' for English, 'es' for Spanish
  const [isAdmin, setIsAdmin] = useState(false);
  // Toggle between user and admin view (in a real app, this would use proper authentication)
  const toggleAdminView = () => {
    setIsAdmin(!isAdmin);
    setCurrentPage(isAdmin ? 'voiceai' : 'admin');
  };
  const renderPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onStart={() => setCurrentPage('form')} language={language} />;
      case 'form':
        return <IntakeForm language={language} />;
      case 'admin':
        return <AdminDashboard language={language} />;
      case 'voiceai':
        return <VoiceAIDashboard />;
      default:
        return <VoiceAIDashboard />;
    }
  };
  return <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={setLanguage} onAdminToggle={toggleAdminView} isAdmin={isAdmin} />
      <main className="container mx-auto px-4 py-8">{renderPage()}</main>
    </div>;
}