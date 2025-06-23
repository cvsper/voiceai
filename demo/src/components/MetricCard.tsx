import React from 'react';
import { BoxIcon } from 'lucide-react';
interface MetricCardProps {
  title: string;
  value: string;
  icon: BoxIcon;
  change?: string;
  isPositive?: boolean;
  status?: 'active' | 'inactive';
}
const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon: Icon,
  change,
  isPositive,
  status
}) => {
  return <div className="rounded-lg bg-gray-800 p-6 transition hover:bg-gray-750">
      <div className="mb-3 flex items-center">
        <div className="rounded-full bg-blue-600/20 p-2">
          <Icon className="h-5 w-5 text-blue-500" />
        </div>
        {status && <div className="ml-auto flex items-center">
            <span className={`h-2 w-2 rounded-full ${status === 'active' ? 'bg-green-500' : 'bg-gray-500'}`}></span>
            <span className="ml-2 text-xs text-gray-400">
              {status === 'active' ? 'Live' : 'Inactive'}
            </span>
          </div>}
      </div>
      <h3 className="text-sm text-gray-400">{title}</h3>
      <div className="mt-1 flex items-end">
        <span className="text-2xl font-bold">{value}</span>
        {change && <div className={`ml-2 flex items-center text-xs ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            {change}
          </div>}
      </div>
    </div>;
};
export default MetricCard;