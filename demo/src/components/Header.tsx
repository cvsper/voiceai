import React from 'react';
import { Globe2Icon, UserIcon } from 'lucide-react';
interface HeaderProps {
  language: string;
  onLanguageChange: (lang: string) => void;
  onAdminToggle: () => void;
  isAdmin: boolean;
}
export const Header: React.FC<HeaderProps> = ({
  language,
  onLanguageChange,
  onAdminToggle,
  isAdmin
}) => {
  const translations = {
    title: {
      en: 'Tax Document Collection',
      es: 'Recolección de Documentos Fiscales'
    },
    admin: {
      en: 'Admin View',
      es: 'Vista de Administrador'
    },
    client: {
      en: 'Client View',
      es: 'Vista de Cliente'
    }
  };
  return <header className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-xl md:text-2xl font-semibold">
          {translations.title[language as keyof typeof translations.title]}
        </h1>
        <div className="flex items-center space-x-4">
          <button onClick={() => onLanguageChange(language === 'en' ? 'es' : 'en')} className="flex items-center text-sm border border-white/30 rounded-full px-3 py-1 hover:bg-blue-700 transition-colors">
            <Globe2Icon className="w-4 h-4 mr-1" />
            {language === 'en' ? 'ES' : 'EN'}
          </button>
          <button onClick={onAdminToggle} className="flex items-center text-sm border border-white/30 rounded-full px-3 py-1 hover:bg-blue-700 transition-colors">
            <UserIcon className="w-4 h-4 mr-1" />
            {isAdmin ? translations.client[language as keyof typeof translations.client] : translations.admin[language as keyof typeof translations.admin]}
          </button>
        </div>
      </div>
    </header>;
};