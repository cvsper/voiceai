import React from 'react';
import { PhoneCallIcon, CalendarIcon, ClockIcon, ActivityIcon, ArrowUpIcon, ArrowDownIcon, CheckCircleIcon, XCircleIcon } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import RecentCallItem from '../components/RecentCallItem';
import { useDashboardMetrics, useRecentCalls, useSystemStatus, useRealTimeUpdates } from '../hooks/useApi';
import apiService from '../services/api';

const Dashboard: React.FC = () => {
  const { data: metricsData, loading: metricsLoading, error: metricsError } = useRealTimeUpdates(
    () => apiService.getDashboardMetrics(),
    10000, // Update every 10 seconds
    true
  );
  const { data: recentCallsData, loading: callsLoading, error: callsError } = useRealTimeUpdates(
    () => apiService.getRecentCalls(5),
    15000, // Update every 15 seconds
    true
  );
  const { data: systemStatusData, loading: statusLoading, error: statusError } = useRealTimeUpdates(
    () => apiService.getSystemStatus(),
    30000, // Update every 30 seconds
    true
  );

  // Transform API data to component format
  const metrics = metricsData ? [
    {
      title: 'Total Calls Today',
      value: metricsData.metrics.total_calls.value.toString(),
      icon: PhoneCallIcon,
      change: `${metricsData.metrics.total_calls.change >= 0 ? '+' : ''}${metricsData.metrics.total_calls.change}%`,
      isPositive: metricsData.metrics.total_calls.change >= 0
    },
    {
      title: 'Appointments Booked',
      value: metricsData.metrics.appointments_booked.value.toString(),
      icon: CalendarIcon,
      change: `${metricsData.metrics.appointments_booked.change >= 0 ? '+' : ''}${metricsData.metrics.appointments_booked.change}%`,
      isPositive: metricsData.metrics.appointments_booked.change >= 0
    },
    {
      title: 'Avg. Call Duration',
      value: metricsData.metrics.avg_call_duration.value,
      icon: ClockIcon,
      change: `${metricsData.metrics.avg_call_duration.change >= 0 ? '+' : ''}${metricsData.metrics.avg_call_duration.change}%`,
      isPositive: metricsData.metrics.avg_call_duration.change >= 0
    },
    {
      title: 'Live Calls',
      value: metricsData.metrics.live_calls.value.toString(),
      icon: ActivityIcon,
      status: metricsData.metrics.live_calls.value > 0 ? 'active' : 'inactive'
    }
  ] : [];

  const recentCalls = recentCallsData?.recent_calls || [];

  // Show loading state
  if (metricsLoading || callsLoading || statusLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (metricsError || callsError || statusError) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6">
        <h2 className="text-red-400 font-semibold mb-2">Error Loading Dashboard</h2>
        <p className="text-gray-300">
          {metricsError || callsError || statusError || 'Failed to load dashboard data'}
        </p>
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
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="mt-3 sm:mt-0">
          <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            New Test Call
          </button>
        </div>
      </div>

      {/* Metrics */}
      <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map(metric => (
          <MetricCard 
            key={metric.title} 
            title={metric.title} 
            value={metric.value} 
            icon={metric.icon} 
            change={metric.change} 
            isPositive={metric.isPositive} 
            status={metric.status} 
          />
        ))}
      </div>

      {/* Quick Stats */}
      <div className="mb-8 grid gap-6 md:grid-cols-2">
        <div className="rounded-lg bg-gray-800 p-6">
          <h2 className="mb-4 text-lg font-semibold">Call Performance</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Answer Rate</span>
              <div className="flex items-center">
                <span className="font-medium">
                  {metricsData?.performance.answer_rate?.toFixed(1) || '0.0'}%
                </span>
                <ArrowUpIcon className="ml-2 h-4 w-4 text-green-500" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Booking Rate</span>
              <div className="flex items-center">
                <span className="font-medium">
                  {metricsData?.performance.booking_rate?.toFixed(1) || '0.0'}%
                </span>
                <ArrowUpIcon className="ml-2 h-4 w-4 text-green-500" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Missed Calls</span>
              <div className="flex items-center">
                <span className="font-medium">
                  {metricsData?.performance.miss_rate?.toFixed(1) || '0.0'}%
                </span>
                <ArrowDownIcon className="ml-2 h-4 w-4 text-green-500" />
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-gray-800 p-6">
          <h2 className="mb-4 text-lg font-semibold">System Status</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Voice AI</span>
              <div className="flex items-center">
                {systemStatusData?.system_status.voice_ai.status === 'operational' ? (
                  <CheckCircleIcon className="mr-2 h-5 w-5 text-green-500" />
                ) : (
                  <XCircleIcon className="mr-2 h-5 w-5 text-red-500" />
                )}
                <span>{systemStatusData?.system_status.voice_ai.message || 'Unknown'}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Call Recording</span>
              <div className="flex items-center">
                {systemStatusData?.system_status.call_recording.status === 'operational' ? (
                  <CheckCircleIcon className="mr-2 h-5 w-5 text-green-500" />
                ) : (
                  <XCircleIcon className="mr-2 h-5 w-5 text-red-500" />
                )}
                <span>{systemStatusData?.system_status.call_recording.message || 'Unknown'}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Calendar Sync</span>
              <div className="flex items-center">
                {systemStatusData?.system_status.calendar_sync.status === 'operational' ? (
                  <CheckCircleIcon className="mr-2 h-5 w-5 text-green-500" />
                ) : (
                  <XCircleIcon className="mr-2 h-5 w-5 text-red-500" />
                )}
                <span>{systemStatusData?.system_status.calendar_sync.message || 'Unknown'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Calls */}
      <div className="rounded-lg bg-gray-800 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent Calls</h2>
          <a href="/call-logs" className="text-sm text-blue-400 hover:text-blue-300">
            View All
          </a>
        </div>
        {recentCalls.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700 text-left text-sm text-gray-400">
                  <th className="pb-3 font-medium">Caller</th>
                  <th className="pb-3 font-medium">Time</th>
                  <th className="pb-3 font-medium">Duration</th>
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {recentCalls.map(call => (
                  <RecentCallItem key={call.id} call={call} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <PhoneCallIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No recent calls found</p>
            <p className="text-sm">Calls will appear here once you start receiving them</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;