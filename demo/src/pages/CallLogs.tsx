import React, { useState } from 'react';
import { SearchIcon, FilterIcon, ChevronLeftIcon, ChevronRightIcon, PlayIcon, DownloadIcon, CalendarIcon, FileTextIcon } from 'lucide-react';
import { useCalls } from '../hooks/useApi';

const CallLogs: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  
  const { data: callsData, loading, error } = useCalls(currentPage, 20, statusFilter || undefined);

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400';
      case 'no-answer':
      case 'busy':
      case 'failed':
        return 'bg-red-500/20 text-red-400';
      case 'in-progress':
      case 'ringing':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  const formatDateTime = (dateTimeString: string) => {
    const date = new Date(dateTimeString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDuration = (duration?: number) => {
    if (!duration) return '0:00';
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getCallType = (callType: string, interactionCount: number) => {
    if (callType === 'conference') return 'Human-Human';
    return interactionCount > 0 ? 'AI' : 'Manual';
  };

  const getDisplayStatus = (status: string, transcriptCount: number) => {
    if (status === 'completed' && transcriptCount > 0) return 'answered';
    if (status === 'completed') return 'answered';
    if (status === 'no-answer') return 'missed';
    if (status === 'busy') return 'busy';
    if (status === 'in-progress') return 'in-progress';
    return status;
  };

  // Filter calls based on search term
  const filteredCalls = callsData?.calls.filter(call => 
    call.from_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    call.call_sid.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading call logs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6">
        <h2 className="text-red-400 font-semibold mb-2">Error Loading Call Logs</h2>
        <p className="text-gray-300">{error}</p>
        <button 
          onClick={() => window.location.reload()} 
          className="mt-4 bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold">Call Logs</h1>
        <div className="mt-3 flex space-x-2 sm:mt-0">
          <div className="relative flex-1">
            <input 
              type="text" 
              placeholder="Search by phone number or call ID..." 
              value={searchTerm} 
              onChange={e => setSearchTerm(e.target.value)} 
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 pl-10 text-sm text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none" 
            />
            <SearchIcon className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          </div>
          <select 
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="no-answer">Missed</option>
            <option value="in-progress">In Progress</option>
            <option value="busy">Busy</option>
          </select>
        </div>
      </div>

      {/* Calls Table */}
      <div className="rounded-lg bg-gray-800 p-6">
        {filteredCalls.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700 text-left text-sm text-gray-400">
                    <th className="pb-3 font-medium">Date/Time</th>
                    <th className="pb-3 font-medium">Caller</th>
                    <th className="pb-3 font-medium">Duration</th>
                    <th className="pb-3 font-medium">Type</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Transcripts</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredCalls.map(call => (
                    <tr key={call.id} className="text-sm">
                      <td className="py-4 font-medium">
                        {formatDateTime(call.start_time)}
                      </td>
                      <td className="py-4">{call.from_number}</td>
                      <td className="py-4">{formatDuration(call.duration)}</td>
                      <td className="py-4">
                        <span className={`rounded px-2 py-1 text-xs ${
                          getCallType(call.call_type, call.interaction_count) === 'AI' 
                            ? 'bg-blue-500/20 text-blue-400' 
                            : 'bg-purple-500/20 text-purple-400'
                        }`}>
                          {getCallType(call.call_type, call.interaction_count)}
                        </span>
                      </td>
                      <td className="py-4">
                        <span className={`rounded px-2 py-1 text-xs ${getStatusClass(call.status)}`}>
                          {getDisplayStatus(call.status, call.transcript_count).charAt(0).toUpperCase() + 
                           getDisplayStatus(call.status, call.transcript_count).slice(1)}
                        </span>
                      </td>
                      <td className="py-4 text-gray-400">
                        {call.transcript_count > 0 ? (
                          <span className="text-blue-400">{call.transcript_count} transcripts</span>
                        ) : (
                          <span>No transcripts</span>
                        )}
                      </td>
                      <td className="py-4">
                        <div className="flex space-x-2">
                          {call.recording_url && (
                            <button 
                              className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" 
                              title="Play Recording"
                              onClick={() => window.open(call.recording_url, '_blank')}
                            >
                              <PlayIcon className="h-4 w-4" />
                            </button>
                          )}
                          {call.recording_url && (
                            <button 
                              className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" 
                              title="Download Recording"
                              onClick={() => {
                                const link = document.createElement('a');
                                link.href = call.recording_url;
                                link.download = `call-${call.call_sid}.mp3`;
                                link.click();
                              }}
                            >
                              <DownloadIcon className="h-4 w-4" />
                            </button>
                          )}
                          <button 
                            className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" 
                            title="View Details"
                            onClick={() => window.open(`/call-details/${call.id}`, '_blank')}
                          >
                            <FileTextIcon className="h-4 w-4" />
                          </button>
                          <button 
                            className="rounded-full bg-gray-700 p-1 hover:bg-gray-600" 
                            title="Schedule Follow-up"
                          >
                            <CalendarIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-400">
                Showing <span className="font-medium">{((currentPage - 1) * 20) + 1}</span> to{' '}
                <span className="font-medium">{Math.min(currentPage * 20, callsData?.total || 0)}</span> of{' '}
                <span className="font-medium">{callsData?.total || 0}</span> results
              </div>
              <div className="flex items-center space-x-2">
                <button 
                  className="flex items-center rounded-lg border border-gray-700 px-3 py-1 text-sm hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed" 
                  disabled={currentPage === 1} 
                  onClick={() => setCurrentPage(currentPage - 1)}
                >
                  <ChevronLeftIcon className="mr-1 h-4 w-4" />
                  Previous
                </button>
                <span className="text-sm text-gray-400">
                  Page {currentPage} of {callsData?.pages || 1}
                </span>
                <button 
                  className="flex items-center rounded-lg border border-gray-700 px-3 py-1 text-sm hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={currentPage >= (callsData?.pages || 1)}
                  onClick={() => setCurrentPage(currentPage + 1)}
                >
                  Next
                  <ChevronRightIcon className="ml-1 h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <FileTextIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No call logs found</h3>
            <p className="text-sm">
              {searchTerm || statusFilter 
                ? 'No calls match your search criteria' 
                : 'Call logs will appear here once you start receiving calls'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CallLogs;