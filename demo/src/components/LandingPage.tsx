import React from 'react';
import { FileTextIcon, ArrowRightIcon } from 'lucide-react';
interface LandingPageProps {
  onStart: () => void;
  language: string;
}
export const LandingPage: React.FC<LandingPageProps> = ({
  onStart,
  language
}) => {
  const translations = {
    title: {
      en: 'Simplify Your Tax Filing Process',
      es: 'Simplifique Su Proceso de Declaración de Impuestos'
    },
    subtitle: {
      en: 'Submit all your tax documents securely in one place',
      es: 'Envíe todos sus documentos fiscales de forma segura en un solo lugar'
    },
    description: {
      en: 'Our easy-to-use platform helps you provide all the information your tax preparer needs, reducing back-and-forth communication and speeding up your tax filing process.',
      es: 'Nuestra plataforma fácil de usar le ayuda a proporcionar toda la información que su preparador de impuestos necesita, reduciendo la comunicación de ida y vuelta y acelerando su proceso de declaración de impuestos.'
    },
    benefits: {
      en: ['Secure document uploads', 'Track your submission progress', 'Receive reminders for missing information', 'Get your refund faster'],
      es: ['Carga segura de documentos', 'Seguimiento del progreso de su presentación', 'Reciba recordatorios para información faltante', 'Obtenga su reembolso más rápido']
    },
    button: {
      en: 'Start Your Tax Filing',
      es: 'Comience Su Declaración de Impuestos'
    }
  };
  return <div className="max-w-4xl mx-auto mt-8 md:mt-16">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="p-8 md:p-12">
          <div className="flex justify-center mb-8">
            <div className="bg-blue-100 p-4 rounded-full">
              <FileTextIcon className="w-12 h-12 text-blue-600" />
            </div>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-center text-gray-800 mb-4">
            {translations.title[language as keyof typeof translations.title]}
          </h1>
          <h2 className="text-xl md:text-2xl text-center text-blue-600 mb-6">
            {translations.subtitle[language as keyof typeof translations.subtitle]}
          </h2>
          <p className="text-gray-600 text-center mb-8 max-w-2xl mx-auto">
            {translations.description[language as keyof typeof translations.description]}
          </p>
          <div className="grid md:grid-cols-2 gap-4 mb-8">
            {translations.benefits[language as keyof typeof translations.benefits].map((benefit, index) => <div key={index} className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                    <span className="text-green-600 text-xs">✓</span>
                  </div>
                </div>
                <p className="ml-3 text-gray-600">{benefit}</p>
              </div>)}
          </div>
          <div className="flex justify-center">
            <button onClick={onStart} className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg flex items-center transition-colors">
              {translations.button[language as keyof typeof translations.button]}
              <ArrowRightIcon className="ml-2 w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>;
};