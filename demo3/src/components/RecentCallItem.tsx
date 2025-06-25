import React from 'react';
import { PlayIcon, DownloadIcon, CalendarIcon } from 'lucide-react';
interface Call {
  id: number;
  caller: string;
  time: string;
  duration: string;
  type: string;
  status: 'answered' | 'missed' | 'booked' | 'in-progress';
}
interface RecentCallItemProps {
  call: Call;
}
const RecentCallItem: React.FC<RecentCallItemProps> = ({
  call
}) => {
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
  return <tr className="text-sm">
      <td className="py-4 font-medium">{call.caller}</td>
      <td className="py-4 text-gray-400">{call.time}</td>
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
      <td className="py-4">
        <div className="flex space-x-2">
          <button className="rounded-full bg-gray-700 p-1 hover:bg-gray-600">
            <PlayIcon className="h-4 w-4" />
          </button>
          <button className="rounded-full bg-gray-700 p-1 hover:bg-gray-600">
            <DownloadIcon className="h-4 w-4" />
          </button>
          <button className="rounded-full bg-gray-700 p-1 hover:bg-gray-600">
            <CalendarIcon className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>;
};
export default RecentCallItem;