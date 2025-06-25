import React, { useState, useEffect } from 'react';
import { 
  PhoneIcon, 
  CalendarIcon, 
  ClockIcon, 
  UserIcon, 
  TrendingUpIcon,
  AlertCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlayIcon,
  RefreshCwIcon,
  SearchIcon
} from 'lucide-react';

interface Call {
  id: number;
  sid: string;
  from_number: string;
  to_number: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  status: string;
  transcript_count?: number;
  latest_transcript?: {
    text: string;
    speaker: string;
    timestamp: string;
  };
}

interface Appointment {
  id: number;
  reference_id: string;
  customer_name: string;
  customer_phone: string;
  service_type?: string;
  appointment_date: string;
  appointment_time: string;
  status: string;
}

interface DashboardMetrics {
  call_metrics: {
    total_calls: number;
    today_calls: number;
    week_calls: number;
    month_calls: number;
    status_breakdown: Record<string, number>;
    average_duration: number;
  };
  appointment_metrics: {
    total_appointments: number;
    today_appointments: number;
    status_breakdown: Record<string, number>;
    conversion_rate: number;
  };
  recent_activity: {
    recent_calls: Call[];
    recent_appointments: Appointment[];
  };
  top_services: Array<{ service: string; count: number }>;
}

export const VoiceAIDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'calls' | 'appointments'>('overview');
  const [testCallNumber, setTestCallNumber] = useState('');

  const API_BASE = 'http://localhost:5001';

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [metricsRes, callsRes, appointmentsRes] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/metrics`),
        fetch(`${API_BASE}/api/calls?per_page=20`),
        fetch(`${API_BASE}/api/appointments?per_page=20`)
      ]);

      const metricsData = await metricsRes.json();
      const callsData = await callsRes.json();
      const appointmentsData = await appointmentsRes.json();

      setMetrics(metricsData);
      setCalls(callsData.calls || []);
      setAppointments(appointmentsData.appointments || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const makeTestCall = async () => {
    if (!testCallNumber) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/test-call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_number: testCallNumber })
      });
      
      const result = await response.json();
      if (result.success) {
        alert(`✅ Test call initiated! Call SID: ${result.call_sid}\n\nYour phone should ring shortly!`);
        setTestCallNumber('');
        setTimeout(fetchDashboardData, 2000); // Refresh data after 2 seconds
      } else {
        let errorMessage = result.error;
        if (errorMessage.includes('not yet verified')) {
          errorMessage = `❌ Phone verification required!\n\nFor trial accounts, you need to verify your phone number in Twilio Console.\n\n🔄 Alternative: Call +18444356005 directly to test the AI!`;
        }
        alert(errorMessage);
      }
    } catch (error) {
      alert('❌ Error making test call - please check your connection');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'scheduled':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'in-progress':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
      case 'failed':
      case 'cancelled':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircleIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatPhoneNumber = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 11 && cleaned.startsWith('1')) {
      return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
    }
    return phone;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCwIcon className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Voice AI Dashboard</h1>
        <p className="text-gray-600">Monitor calls, appointments, and AI assistant performance</p>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <PhoneIcon className="w-8 h-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.call_metrics.total_calls}</p>
                <p className="text-xs text-gray-500">Today: {metrics.call_metrics.today_calls}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <CalendarIcon className="w-8 h-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Appointments</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.appointment_metrics.total_appointments}</p>
                <p className="text-xs text-gray-500">Today: {metrics.appointment_metrics.today_appointments}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <TrendingUpIcon className="w-8 h-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.appointment_metrics.conversion_rate}%</p>
                <p className="text-xs text-gray-500">Appointments per call</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <ClockIcon className="w-8 h-8 text-orange-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Duration</p>
                <p className="text-2xl font-bold text-gray-900">{formatDuration(Math.round(metrics.call_metrics.average_duration))}</p>
                <p className="text-xs text-gray-500">Per call</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Test Call Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Voice AI</h3>
        
        {/* Outbound Test */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-700 mb-2">Outbound Test Call</h4>
          <div className="flex items-center space-x-4 mb-2">
            <input
              type="tel"
              placeholder="Enter your phone number (e.g., +15551234567)"
              value={testCallNumber}
              onChange={(e) => setTestCallNumber(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={makeTestCall}
              disabled={!testCallNumber}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <PlayIcon className="w-4 h-4 mr-2" />
              Call Me
            </button>
          </div>
          <p className="text-xs text-gray-500">Note: May require phone number verification for trial accounts</p>
        </div>

        {/* Inbound Test */}
        <div className="border-t pt-4">
          <h4 className="text-md font-medium text-gray-700 mb-2">Inbound Test (Recommended)</h4>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <PhoneIcon className="w-5 h-5 text-green-600 mr-2" />
              <span className="font-medium text-green-800">Call: +18444356005</span>
            </div>
            <p className="text-sm text-green-700">Call this number directly to test the AI assistant. Try saying:</p>
            <ul className="text-sm text-green-600 mt-2 ml-4">
              <li>• "I'd like to book an appointment"</li>
              <li>• "What times are available tomorrow?"</li>
              <li>• "Can you help me schedule a meeting?"</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'calls', label: 'Recent Calls' },
            { id: 'appointments', label: 'Appointments' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'overview' && metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Calls */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Calls</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {metrics.recent_activity.recent_calls.slice(0, 5).map((call) => (
                  <div key={call.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(call.status)}
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {formatPhoneNumber(call.from_number)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(call.start_time).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-900">{formatDuration(call.duration)}</p>
                      <p className="text-xs text-gray-500 capitalize">{call.status}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Appointments */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Appointments</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {metrics.recent_activity.recent_appointments.slice(0, 5).map((appointment) => (
                  <div key={appointment.id} className="flex items-center justify-between">
                    <div className="flex items-center">
                      {getStatusIcon(appointment.status)}
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {appointment.customer_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {appointment.service_type || 'General appointment'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-900">
                        {new Date(appointment.appointment_date).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500">
                        {appointment.appointment_time}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'calls' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Call History</h3>
              <div className="relative">
                <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search calls..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Call</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Transcript</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {calls.filter(call => 
                  call.from_number.includes(searchTerm) || 
                  call.to_number.includes(searchTerm) ||
                  call.sid.includes(searchTerm)
                ).map((call) => (
                  <tr key={call.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {formatPhoneNumber(call.from_number)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(call.start_time).toLocaleString()}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDuration(call.duration)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(call.status)}
                        <span className="ml-2 text-sm capitalize">{call.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {call.latest_transcript ? (
                        <p className="text-sm text-gray-600 truncate max-w-xs">
                          {call.latest_transcript.text}
                        </p>
                      ) : (
                        <span className="text-xs text-gray-400">No transcript</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'appointments' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Appointments</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date & Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {appointments.map((appointment) => (
                  <tr key={appointment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {appointment.customer_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatPhoneNumber(appointment.customer_phone)}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {appointment.service_type || 'General'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-sm text-gray-900">
                          {new Date(appointment.appointment_date).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-gray-500">
                          {appointment.appointment_time}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(appointment.status)}
                        <span className="ml-2 text-sm capitalize">{appointment.status}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};