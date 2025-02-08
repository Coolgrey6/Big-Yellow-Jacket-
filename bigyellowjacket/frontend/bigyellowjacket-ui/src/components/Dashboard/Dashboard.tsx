// src/components/Dashboard/Dashboard.tsx

import React from 'react';
import { Shield, Activity, Globe, Cpu, AlertCircle } from 'lucide-react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { formatBytes } from '../../utils/formatBytes';
import AlertCard from './AlertCard';

interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  trend: string;
  trendUp: boolean;
}

export const Dashboard: React.FC = () => {
  const { connected, metrics, connections, alerts } = useWebSocket();

  // Calculate trends (mock for now, could be calculated from historical data)
  const getTrend = (current: number, baseline: number = 0) => {
    const diff = current - baseline;
    const percentage = baseline ? (diff / baseline) * 100 : 0;
    return {
      value: `${percentage >= 0 ? '+' : ''}${percentage.toFixed(1)}%`,
      up: percentage >= 0
    };
  };

  // Safely access metrics with default values
  const cpuPercent = metrics?.system?.cpu?.percent ?? 0;
  const networkBytesRecv = metrics?.system?.network?.bytes_recv ?? 0;
  const networkBytesSent = metrics?.system?.network?.bytes_sent ?? 0;
  const bytesMonitored = metrics?.traffic?.bytes_monitored ?? 0;
  
  // Calculate network load
  const networkLoad = (networkBytesRecv + networkBytesSent) / 1024 / 1024; // MB
  const totalTraffic = formatBytes(bytesMonitored);
  const activeConnections = connections?.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">System Overview</h2>
        <div className="flex items-center space-x-2 text-sm">
          <span className={connected ? "text-green-500" : "text-red-500"}>●</span>
          <span>{connected ? "Monitoring Active" : "Disconnected"}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Shield className="w-8 h-8 text-green-500" />}
          title="Active Connections"
          value={activeConnections.toString()}
          trend={getTrend(activeConnections).value}
          trendUp={getTrend(activeConnections).up}
        />
        <MetricCard
          icon={<Activity className="w-8 h-8 text-blue-500" />}
          title="Network Load"
          value={`${networkLoad.toFixed(2)} MB`}
          trend={getTrend(networkLoad).value}
          trendUp={getTrend(networkLoad).up}
        />
        <MetricCard
          icon={<Globe className="w-8 h-8 text-purple-500" />}
          title="Total Traffic"
          value={totalTraffic}
          trend={getTrend(bytesMonitored).value}
          trendUp={getTrend(bytesMonitored).up}
        />
        <MetricCard
          icon={<Cpu className="w-8 h-8 text-orange-500" />}
          title="System Load"
          value={`${cpuPercent.toFixed(1)}%`}
          trend={getTrend(cpuPercent).value}
          trendUp={getTrend(cpuPercent).up}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <AlertCard alerts={alerts || []} />
        <ConnectionsCard connections={connections || []} />
        <SystemStatusCard metrics={metrics} />
      </div>
    </div>
  );
};

const MetricCard: React.FC<MetricCardProps> = ({ icon, title, value, trend, trendUp }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-gray-500 text-sm">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
      </div>
      {icon}
    </div>
    <div className={`mt-2 text-sm ${trendUp ? 'text-green-500' : 'text-red-500'}`}>
      {trend} from last hour
    </div>
  </div>
);

const ConnectionsCard = ({ connections }: { connections: any[] }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
    <h3 className="font-medium mb-4">Active Connections</h3>
    <div className="space-y-2">
      {connections.slice(0, 5).map((conn, index) => (
        <div key={index} className="text-sm flex justify-between">
          <span>{conn.host}:{conn.port}</span>
          <span className={`px-2 py-0.5 rounded-full text-xs ${
            conn.status === 'SAFE' ? 'bg-green-100 text-green-800' :
            conn.status === 'SUSPICIOUS' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {conn.status}
          </span>
        </div>
      ))}
      {connections.length === 0 && (
        <div className="text-gray-500 text-sm">No active connections</div>
      )}
    </div>
  </div>
);

const SystemStatusCard = ({ metrics }: { metrics: any }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
    <h3 className="font-medium mb-4">System Status</h3>
    <div className="space-y-3">
      <div className="flex justify-between text-sm">
        <span>CPU Usage</span>
        <span>{(metrics?.system?.cpu?.percent ?? 0).toFixed(1)}%</span>
      </div>
      <div className="flex justify-between text-sm">
        <span>Memory Usage</span>
        <span>{(metrics?.system?.memory?.percent ?? 0).toFixed(1)}%</span>
      </div>
      <div className="flex justify-between text-sm">
        <span>Network In</span>
        <span>{formatBytes(metrics?.system?.network?.bytes_recv ?? 0)}/s</span>
      </div>
      <div className="flex justify-between text-sm">
        <span>Network Out</span>
        <span>{formatBytes(metrics?.system?.network?.bytes_sent ?? 0)}/s</span>
      </div>
    </div>
  </div>
);