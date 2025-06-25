import React from 'react';
import { CheckCircleIcon, XCircleIcon, AlertCircleIcon } from 'lucide-react';
interface ChecklistItem {
  id: string;
  label: {
    en: string;
    es: string;
  };
  completed: boolean;
  required: boolean;
}
interface ProgressChecklistProps {
  items: ChecklistItem[];
  language: string;
}
export const ProgressChecklist: React.FC<ProgressChecklistProps> = ({
  items,
  language
}) => {
  const translations = {
    title: {
      en: 'Your Progress',
      es: 'Su Progreso'
    },
    complete: {
      en: 'Complete',
      es: 'Completo'
    },
    missing: {
      en: 'Missing',
      es: 'Faltante'
    },
    optional: {
      en: 'Optional',
      es: 'Opcional'
    }
  };
  const completedCount = items.filter(item => item.completed).length;
  const requiredCount = items.filter(item => item.required).length;
  const requiredCompletedCount = items.filter(item => item.required && item.completed).length;
  const progress = requiredCount > 0 ? Math.round(requiredCompletedCount / requiredCount * 100) : 0;
  return <div className="bg-white rounded-lg shadow p-6 mb-8">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">
        {translations.title[language as keyof typeof translations.title]} (
        {completedCount}/{items.length})
      </h2>
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-6">
        <div className="bg-blue-600 h-2.5 rounded-full" style={{
        width: `${progress}%`
      }}></div>
      </div>
      <ul className="space-y-3">
        {items.map(item => <li key={item.id} className="flex items-center">
            {item.completed ? <CheckCircleIcon className="w-5 h-5 text-green-500 mr-3" /> : item.required ? <XCircleIcon className="w-5 h-5 text-red-500 mr-3" /> : <AlertCircleIcon className="w-5 h-5 text-yellow-500 mr-3" />}
            <span className={`${item.completed ? 'text-gray-800' : 'text-gray-600'}`}>
              {item.label[language as keyof typeof item.label]}
            </span>
            <span className="ml-auto text-xs px-2 py-1 rounded-full font-medium">
              {item.completed ? <span className="text-green-600 bg-green-100 px-2 py-1 rounded-full">
                  {translations.complete[language as keyof typeof translations.complete]}
                </span> : item.required ? <span className="text-red-600 bg-red-100 px-2 py-1 rounded-full">
                  {translations.missing[language as keyof typeof translations.missing]}
                </span> : <span className="text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full">
                  {translations.optional[language as keyof typeof translations.optional]}
                </span>}
            </span>
          </li>)}
      </ul>
    </div>;
};