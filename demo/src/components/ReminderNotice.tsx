import React from 'react';
import { BellIcon } from 'lucide-react';
interface ReminderNoticeProps {
  language: string;
}
export const ReminderNotice: React.FC<ReminderNoticeProps> = ({
  language
}) => {
  const translations = {
    title: {
      en: 'Automatic Reminders',
      es: 'Recordatorios Automáticos'
    },
    message: {
      en: 'You will receive email and SMS reminders if any information is incomplete or additional documents are needed.',
      es: 'Recibirá recordatorios por correo electrónico y SMS si falta información o se necesitan documentos adicionales.'
    }
  };
  return <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start">
      <div className="bg-yellow-100 p-2 rounded-full mr-4">
        <BellIcon className="w-6 h-6 text-yellow-600" />
      </div>
      <div>
        <h3 className="font-medium text-yellow-800 mb-1">
          {translations.title[language as keyof typeof translations.title]}
        </h3>
        <p className="text-yellow-700 text-sm">
          {translations.message[language as keyof typeof translations.message]}
        </p>
      </div>
    </div>;
};