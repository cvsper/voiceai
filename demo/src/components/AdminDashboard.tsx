import React, { useState } from 'react';
import { DownloadIcon, CheckCircleIcon, AlertCircleIcon, XCircleIcon, SearchIcon } from 'lucide-react';
interface AdminDashboardProps {
  language: string;
}
interface ClientData {
  id: number;
  name: string;
  email: string;
  status: 'complete' | 'partial' | 'not_started';
  lastUpdated: string;
  documentsCount: number;
}
export const AdminDashboard: React.FC<AdminDashboardProps> = ({
  language
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const translations = {
    title: {
      en: 'Tax Preparer Dashboard',
      es: 'Panel del Preparador de Impuestos'
    },
    subtitle: {
      en: 'Monitor and manage client tax document submissions',
      es: 'Monitorear y gestionar las presentaciones de documentos fiscales de los clientes'
    },
    search: {
      en: 'Search clients...',
      es: 'Buscar clientes...'
    },
    clientsTable: {
      en: {
        name: 'Client Name',
        status: 'Status',
        lastUpdated: 'Last Updated',
        documents: 'Documents',
        actions: 'Actions'
      },
      es: {
        name: 'Nombre del Cliente',
        status: 'Estado',
        lastUpdated: 'Última Actualización',
        documents: 'Documentos',
        actions: 'Acciones'
      }
    },
    status: {
      en: {
        complete: 'Complete',
        partial: 'In Progress',
        not_started: 'Not Started'
      },
      es: {
        complete: 'Completo',
        partial: 'En Progreso',
        not_started: 'No Iniciado'
      }
    },
    actions: {
      en: {
        download: 'Download',
        view: 'View Details'
      },
      es: {
        download: 'Descargar',
        view: 'Ver Detalles'
      }
    },
    summary: {
      en: {
        title: 'Summary',
        total: 'Total Clients',
        complete: 'Complete Submissions',
        partial: 'Partial Submissions',
        notStarted: 'Not Started'
      },
      es: {
        title: 'Resumen',
        total: 'Total de Clientes',
        complete: 'Presentaciones Completas',
        partial: 'Presentaciones Parciales',
        notStarted: 'No Iniciado'
      }
    }
  };
  // Mock client data
  const clients: ClientData[] = [{
    id: 1,
    name: 'John Smith',
    email: 'john@example.com',
    status: 'complete',
    lastUpdated: '2023-05-10',
    documentsCount: 5
  }, {
    id: 2,
    name: 'Maria Garcia',
    email: 'maria@example.com',
    status: 'partial',
    lastUpdated: '2023-05-09',
    documentsCount: 3
  }, {
    id: 3,
    name: 'Robert Johnson',
    email: 'robert@example.com',
    status: 'not_started',
    lastUpdated: '2023-05-01',
    documentsCount: 0
  }, {
    id: 4,
    name: 'Sofia Rodriguez',
    email: 'sofia@example.com',
    status: 'complete',
    lastUpdated: '2023-05-08',
    documentsCount: 7
  }, {
    id: 5,
    name: 'Michael Wilson',
    email: 'michael@example.com',
    status: 'partial',
    lastUpdated: '2023-05-07',
    documentsCount: 2
  }];
  // Filter clients based on search term
  const filteredClients = clients.filter(client => client.name.toLowerCase().includes(searchTerm.toLowerCase()) || client.email.toLowerCase().includes(searchTerm.toLowerCase()));
  // Calculate summary statistics
  const totalClients = clients.length;
  const completeSubmissions = clients.filter(client => client.status === 'complete').length;
  const partialSubmissions = clients.filter(client => client.status === 'partial').length;
  const notStartedSubmissions = clients.filter(client => client.status === 'not_started').length;
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'partial':
        return <AlertCircleIcon className="w-5 h-5 text-yellow-500" />;
      case 'not_started':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };
  return <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6 md:p-8 mb-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          {translations.title[language as keyof typeof translations.title]}
        </h1>
        <p className="text-gray-600 mb-8">
          {translations.subtitle[language as keyof typeof translations.subtitle]}
        </p>
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">
              {translations.summary[language as keyof typeof translations.summary].total}
            </h3>
            <p className="text-2xl font-bold text-blue-600">{totalClients}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-green-800">
              {translations.summary[language as keyof typeof translations.summary].complete}
            </h3>
            <p className="text-2xl font-bold text-green-600">
              {completeSubmissions}
            </p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-800">
              {translations.summary[language as keyof typeof translations.summary].partial}
            </h3>
            <p className="text-2xl font-bold text-yellow-600">
              {partialSubmissions}
            </p>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-red-800">
              {translations.summary[language as keyof typeof translations.summary].notStarted}
            </h3>
            <p className="text-2xl font-bold text-red-600">
              {notStartedSubmissions}
            </p>
          </div>
        </div>
        <div className="mb-6">
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input type="text" placeholder={translations.search[language as keyof typeof translations.search]} value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 text-left">
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {translations.clientsTable[language as keyof typeof translations.clientsTable].name}
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {translations.clientsTable[language as keyof typeof translations.clientsTable].status}
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {translations.clientsTable[language as keyof typeof translations.clientsTable].lastUpdated}
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {translations.clientsTable[language as keyof typeof translations.clientsTable].documents}
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {translations.clientsTable[language as keyof typeof translations.clientsTable].actions}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredClients.map(client => <tr key={client.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="font-medium text-gray-800">
                        {client.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {client.email}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(client.status)}
                      <span className="ml-2">
                        {translations.status[language as keyof typeof translations.status][client.status as keyof (typeof translations.status)[keyof typeof translations.status]]}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {client.lastUpdated}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {client.documentsCount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex space-x-2">
                      <button className="text-blue-600 hover:text-blue-800 font-medium text-sm flex items-center" disabled={client.status === 'not_started'}>
                        <DownloadIcon className="w-4 h-4 mr-1" />
                        {translations.actions[language as keyof typeof translations.actions].download}
                      </button>
                      <button className="text-gray-600 hover:text-gray-800 font-medium text-sm">
                        {translations.actions[language as keyof typeof translations.actions].view}
                      </button>
                    </div>
                  </td>
                </tr>)}
            </tbody>
          </table>
        </div>
      </div>
    </div>;
};