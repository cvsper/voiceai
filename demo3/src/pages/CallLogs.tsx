import React, { useState } from 'react';
import { SearchIcon, FilterIcon, ChevronLeftIcon, ChevronRightIcon, PlayIcon, DownloadIcon, CalendarIcon, FileTextIcon } from 'lucide-react';
const CallLogs: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  // Mock data
  const calls = [{
    id: 1,
    dateTime: '2023-06-15 09:23 AM',
    caller: '+1 (555) 123-4567',
    duration: '3:45',
    type: 'AI',
    status: 'answered',
    transcript: "Hi, I'm calling to schedule an appointment for..."
  }, {
    id: 2,
    dateTime: '2023-06-15 10:15 AM',
    caller: '+1 (555) 987-6543',
    duration: '2:12',
    type: 'AI',
    status: 'booked',
    transcript: "Yes, I'd like to book a consultation for next week..."
  }, {
    id: 3,
    dateTime: '2023-06-15 11:32 AM',
    caller: '+1 (555) 456-7890',
    duration: '1:05',
    type: 'Human-Human',
    status: 'missed',
    transcript: 'This is John from Acme Corp, I wanted to discuss...'
  }, {
    id: 4,
    dateTime: '2023-06-15 01:47 PM',
    caller: '+1 (555) 234-5678',
    duration: '4:23',
    type: 'AI',
    status: 'answered',
    transcript: "I'm interested in your services. Can you tell me more about..."
  }, {
    id: 5,
    dateTime: '2023-06-15 02:30 PM',
    caller: '+1 (555) 345-6789',
    duration: '5:18',
    type: 'Human-Human',
    status: 'booked',
    transcript: 'I saw your website and wanted to inquire about pricing...'
  }, {
    id: 6,
    dateTime: '2023-06-15 03:15 PM',
    caller: '+1 (555) 876-5432',
    duration: '2:56',
    type: 'AI',
    status: 'answered',
    transcript: 'Hello, I need some information about your business hours...'
  }, {
    id: 7,
    dateTime: '2023-06-15 04:02 PM',
    caller: '+1 (555) 765-4321',
    duration: '0:45',
    type: 'AI',
    status: 'missed',
    transcript: 'This is Sarah calling about the quote you sent last week...'
  }];
  const getStatusClass = (status: string) => {
    switch (status) {
      case 'answered':
        return 'bg-green-500/20 text-green-400';
      case 'missed':
        return 'bg-red-500/20 text-red-400';
      case 'booked':
        return 'bg-blue-500/20 text-blue-400';
      case 'in-progress':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };
  return <div>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold">Call Logs</h1>
        <div className="mt-3 flex space-x-2 sm:mt-0">
          <div className="relative flex-1">
            <input type="text" placeholder="Search calls..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 pl-10 text-sm text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none" />
            <SearchIcon className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          </div>
          <button className="flex items-center rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm hover:bg-gray-700">
            <FilterIcon className="mr-2 h-4 w-4" />
            Filter
          </button>
        </div>
      </div>
      {/* Calls Table */}
      <div className="rounded-lg bg-gray-800 p-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700 text-left text-sm text-gray-400">
                <th className="pb-3 font-medium">Date/Time</th>
                <th className="pb-3 font-medium">Caller</th>
                <th className="pb-3 font-medium">Duration</th>
                <th className="pb-3 font-medium">Type</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Transcript</th>
                <th className="pb-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {calls.map(call => <tr key={call.id} className="text-sm">
                  <td className="py-4 font-medium">{call.dateTime}</td>
                  <td className="py-4">{call.caller}</td>
                  <td className="py-4">{call.duration}</td>
                  <td className="py-4">
                    <span className={`rounded px-2 py-1 text-xs ${call.type === 'AI' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}`}>
                      {call.type}
                    </span>
                  </td>
                  <td className="py-4">
                    <span className={`rounded px-2 py-1 text-xs ${getStatusClass(call.status)}`}>
                      {call.status.charAt(0).toUpperCase() + call.status.slice(1)}
                    </span>
                  </td>
                  <td className="max-w-xs truncate py-4 text-gray-400">
                    {call.transcript}
                  </td>
                  <td className="py-4">
                    <div className="flex space-x-2">
                      <button className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" title="Play Recording">
                        <PlayIcon className="h-4 w-4" />
                      </button>
                      <button className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" title="Download Recording">
                        <DownloadIcon className="h-4 w-4" />
                      </button>
                      <button className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" title="View Transcript">
                        <FileTextIcon className="h-4 w-4" />
                      </button>
                      <button className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" title="Schedule Follow-up">
                        <CalendarIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>)}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            Showing <span className="font-medium">1</span> to{' '}
            <span className="font-medium">7</span> of{' '}
            <span className="font-medium">42</span> results
          </div>
          <div className="flex items-center space-x-2">
            <button className="flex items-center rounded-lg border border-gray-700 px-3 py-1 text-sm hover:bg-gray-700" disabled={currentPage === 1} onClick={() => setCurrentPage(currentPage - 1)}>
              <ChevronLeftIcon className="mr-1 h-4 w-4" />
              Previous
            </button>
            <button className="flex items-center rounded-lg border border-gray-700 px-3 py-1 text-sm hover:bg-gray-700" onClick={() => setCurrentPage(currentPage + 1)}>
              Next
              <ChevronRightIcon className="ml-1 h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>;
};
export default CallLogs;