import React from 'react';
import { LinkIcon } from 'lucide-react';
interface PaymentInstructionsProps {
  language: string;
}
export const PaymentInstructions: React.FC<PaymentInstructionsProps> = ({
  language
}) => {
  const translations = {
    title: {
      en: 'IRS Payment Instructions',
      es: 'Instrucciones de Pago del IRS'
    },
    subtitle: {
      en: 'If you need to make a payment to the IRS, use the following official links:',
      es: 'Si necesita realizar un pago al IRS, utilice los siguientes enlaces oficiales:'
    },
    english: {
      en: 'English',
      es: 'Inglés'
    },
    spanish: {
      en: 'Spanish',
      es: 'Español'
    }
  };
  return <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 my-8">
      <h3 className="font-semibold text-blue-800 text-lg mb-2">
        {translations.title[language as keyof typeof translations.title]}
      </h3>
      <p className="text-blue-700 mb-4">
        {translations.subtitle[language as keyof typeof translations.subtitle]}
      </p>
      <div className="space-y-3">
        <a href="https://www.irs.gov/payments" target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:text-blue-800 hover:underline font-medium">
          <LinkIcon className="w-5 h-5 mr-2" />
          irs.gov/payments (
          {translations.english[language as keyof typeof translations.english]})
        </a>
        <a href="https://www.irs.gov/es/payments" target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:text-blue-800 hover:underline font-medium">
          <LinkIcon className="w-5 h-5 mr-2" />
          irs.gov/pagos (
          {translations.spanish[language as keyof typeof translations.spanish]})
        </a>
      </div>
    </div>;
};