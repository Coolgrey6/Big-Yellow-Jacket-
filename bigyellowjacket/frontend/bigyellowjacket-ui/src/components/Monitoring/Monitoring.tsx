import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Cpu, Database, HardDrive, Network, Play, Pause, RefreshCw } from 'lucide-react';
import { useWebSocket, useWebSocketStore } from '../../hooks/useWebSocket';
import { formatBytes } from '../../utils/formatBytes';

export const Monitoring: React.FC = () => {
  const { connected, send } = useWebSocket();
  const { metrics } = useWebSocketStore();
  const [monitoringEnabled, setMonitoringEnabled] = useState(true);
  const [metricsHistory, setMetricsHistory] = useState<any[]>([]);

  // Update metrics history when new metrics arrive
  useEffect(() => {
    if (metrics?.system) {
      const newMetric = {
        timestamp: new Date().toLocaleTimeString(),
        cpu: metrics.system.cpu || 0,
        memory: metrics.system.memory?.percent || 0,
        networkIn: metrics.system.network?.bytes_recv || 0,
        networkOut: metrics.system.network?.bytes_sent || 0
      };

      setMetricsHistory(prev => [...prev.slice(-20), newMetric]); // Keep last 20 data points
    }
  }, [metrics]);

  const toggleMonitoring = () => {
    setMonitoringEnabled(!monitoringEnabled);
    send({ 
      command: monitoringEnabled ? 'pause_monitoring' : 'resume_monitoring' 
    });
  };

  const refreshMetrics = () => {
    send({ command: 'refresh_metrics' });
  };

  const systemMetrics = {
    cpu: {
      usage: metrics?.system?.cpu || 0,
      cores: metrics?.system?.cpu?.cores || 0,
      frequency: metrics?.system?.cpu?.frequency || 0
    },
    memory: {
      used: metrics?.system?.memory?.used || 0,
      total: metrics?.system?.memory?.total || 0,
      percent: metrics?.system?.memory?.percent || 0
    },
    disk: {
      used: metrics?.system?.disk?.used || 0,
      total: metrics?.system?.disk?.total || 0,
      percent: metrics?.system?.disk?.percent || 0
    },
    network: {
      bytesReceived: metrics?.system?.network?.bytes_recv || 0,
      bytesSent: metrics?.system?.network?.bytes_sent || 0
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">System Monitoring</h2>
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleMonitoring}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
              monitoringEnabled 
                ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            {monitoringEnabled ? (
              <>
                <Pause className="w-4 h-4" />
                <span>Pause Monitoring</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Resume Monitoring</span>
              </>
            )}
          </button>
          <button
            onClick={refreshMetrics}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricBox
          icon={<Cpu className="w-6 h-6 text-blue-500" />}
          title="CPU Usage"
          value={`${systemMetrics.cpu.usage.toFixed(1)}%`}
          details={[
            `Cores: ${systemMetrics.cpu.cores}`,
            `Frequency: ${systemMetrics.cpu.frequency.toFixed(1)} MHz`
          ]}
        />
        <MetricBox
          icon={<Database className="w-6 h-6 text-green-500" />}
          title="Memory Usage"
          value={`${systemMetrics.memory.percent.toFixed(1)}%`}
          details={[
            `Used: ${formatBytes(systemMetrics.memory.used)}`,
            `Total: ${formatBytes(systemMetrics.memory.total)}`
          ]}
        />
        <MetricBox
          icon={<HardDrive className="w-6 h-6 text-purple-500" />}
          title="Disk Usage"
          value={`${systemMetrics.disk.percent.toFixed(1)}%`}
          details={[
            `Used: ${formatBytes(systemMetrics.disk.used)}`,
            `Total: ${formatBytes(systemMetrics.disk.total)}`
          ]}
        />
        <MetricBox
          icon={<Network className="w-6 h-6 text-orange-500" />}
          title="Network Traffic"
          value={`${formatBytes(systemMetrics.network.bytesReceived)}/s`}
          details={[
            `In: ${formatBytes(systemMetrics.network.bytesReceived)}/s`,
            `Out: ${formatBytes(systemMetrics.network.bytesSent)}/s`
          ]}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium mb-4">CPU & Memory Trends</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metricsHistory} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="cpu" 
                  stroke="#3B82F6" 
                  name="CPU %" 
                  dot={false}
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="memory" 
                  stroke="#10B981" 
                  name="Memory %" 
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-medium mb-4">Network Traffic</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metricsHistory} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="networkIn" 
                  stroke="#8B5CF6" 
                  name="Received" 
                  dot={false}
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="networkOut" 
                  stroke="#EC4899" 
                  name="Sent" 
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

interface MetricBoxProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  details: string[];
}

const MetricBox: React.FC<MetricBoxProps> = ({ icon, title, value, details }) => (
  <div className="bg-white p-4 rounded-lg shadow-sm">
    <div className="flex items-start justify-between">
      <div>
        <h3 className="text-gray-500 text-sm">{title}</h3>
        <p className="text-2xl font-bold mt-1">{value}</p>
      </div>
      {icon}
    </div>
    <div className="mt-4 space-y-1">
      {details.map((detail, index) => (
        <p key={index} className="text-sm text-gray-500">{detail}</p>
      ))}
    </div>
  </div>
);