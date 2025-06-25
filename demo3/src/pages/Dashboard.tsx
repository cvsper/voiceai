import React from 'react';
import { PhoneCallIcon, CalendarIcon, ClockIcon, ActivityIcon, ArrowUpIcon, ArrowDownIcon, CheckCircleIcon, XCircleIcon } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import RecentCallItem from '../components/RecentCallItem';
const Dashboard: React.FC = () => {
  // Mock data for the dashboard
  const metrics = [{
    title: 'Total Calls Today',
    value: '24',
    icon: PhoneCallIcon,
    change: '+12%',
    isPositive: true
  }, {
    title: 'Appointments Booked',
    value: '8',
    icon: CalendarIcon,
    change: '+33%',
    isPositive: true
  }, {
    title: 'Avg. Call Duration',
    value: '3:24',
    icon: ClockIcon,
    change: '-8%',
    isPositive: true
  }, {
    title: 'Live Calls',
    value: '2',
    icon: ActivityIcon,
    status: 'active'
  }];
  const recentCalls = [{
    id: 1,
    caller: '+1 (555) 123-4567',
    time: '10 mins ago',
    duration: '2:34',
    type: 'AI',
    status: 'answered'
  }, {
    id: 2,
    caller: '+1 (555) 987-6543',
    time: '32 mins ago',
    duration: '4:12',
    type: 'AI',
    status: 'booked'
  }, {
    id: 3,
    caller: '+1 (555) 456-7890',
    time: '1 hour ago',
    duration: '1:05',
    type: 'Human-Human',
    status: 'missed'
  }, {
    id: 4,
    caller: '+1 (555) 234-5678',
    time: '3 hours ago',
    duration: '5:47',
    type: 'AI',
    status: 'answered'
  }];
  return <div>
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
        {metrics.map(metric => <MetricCard key={metric.title} title={metric.title} value={metric.value} icon={metric.icon} change={metric.change} isPositive={metric.isPositive} status={metric.status} />)}
      </div>
      {/* Quick Stats */}
      <div className="mb-8 grid gap-6 md:grid-cols-2">
        <div className="rounded-lg bg-gray-800 p-6">
          <h2 className="mb-4 text-lg font-semibold">Call Performance</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Answer Rate</span>
              <div className="flex items-center">
                <span className="font-medium">87%</span>
                <ArrowUpIcon className="ml-2 h-4 w-4 text-green-500" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Booking Rate</span>
              <div className="flex items-center">
                <span className="font-medium">32%</span>
                <ArrowUpIcon className="ml-2 h-4 w-4 text-green-500" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Missed Calls</span>
              <div className="flex items-center">
                <span className="font-medium">8%</span>
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
                <CheckCircleIcon className="mr-2 h-5 w-5 text-green-500" />
                <span>Operational</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Call Recording</span>
              <div className="flex items-center">
                <CheckCircleIcon className="mr-2 h-5 w-5 text-green-500" />
                <span>Operational</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Calendar Sync</span>
              <div className="flex items-center">
                <XCircleIcon className="mr-2 h-5 w-5 text-red-500" />
                <span>Issue Detected</span>
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
              {recentCalls.map(call => <RecentCallItem key={call.id} call={call} />)}
            </tbody>
          </table>
        </div>
      </div>
    </div>;
};
export default Dashboard;