import React, { useState, useEffect } from 'react';
import { Shield, Activity, Globe, AlertCircle, Database, Lock, Unlock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useWebSocket, useWebSocketStore } from '../../hooks/useWebSocket';

interface Connection {
  host: string;
  port: number;
  protocol: string;
  processName?: string;
  status: string;
  bytesSent: number;
  bytesReceived: number;
  latency: number;
  processInfo?: {
    name: string;
    path: string;
    pid?: number;
    username?: string;
    cpu_percent?: number;
    memory_percent?: number;
    status?: string;
  };
  last_seen?: string;
}

export const NetworkIntelligence: React.FC = () => {
  const { connected, error, send } = useWebSocket();
  const connections = useWebSocketStore((state) => state.connections);
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  const [page, setPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'host' | 'status' | 'latency'>('host');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [blockedIPs, setBlockedIPs] = useState<Set<string>>(new Set());

  // Request initial data when connected
  useEffect(() => {
    if (connected) {
      send({ command: 'get_connections' });
    }
  }, [connected, send]);

  // Function to handle blocking an IP
  const handleBlock = (connection: Connection) => {
    send({
      command: 'block_ip',
      params: { host: connection.host }
    });
    setBlockedIPs(prev => new Set([...prev, connection.host]));
    // If the blocked connection is selected, close the modal
    if (selectedConnection?.host === connection.host) {
      setSelectedConnection(null);
    }
  };

  // Function to handle unblocking an IP
  const handleUnblock = (connection: Connection) => {
    send({
      command: 'unblock_ip',
      params: { host: connection.host }
    });
    setBlockedIPs(prev => {
      const newSet = new Set(prev);
      newSet.delete(connection.host);
      return newSet;
    });
  };

  // Format process info for display
  const getProcessDisplay = (connection: Connection): string => {
    if (connection.processInfo?.name) {
      const pid = connection.processInfo.pid ? ` (PID: ${connection.processInfo.pid})` : '';
      const user = connection.processInfo.username ? ` - User: ${connection.processInfo.username}` : '';
      return `${connection.processInfo.name}${pid}${user}`;
    }
    return connection.processName || 'Unknown';
  };

  const formatBytes = (bytes: number | undefined): string => {
    if (typeof bytes !== 'number' || isNaN(bytes)) return '0 B';
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  // Filter and sort connections
  const filteredConnections = connections
    .filter(conn =>
      conn.host.toLowerCase().includes(searchTerm.toLowerCase()) ||
      getProcessDisplay(conn).toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'host') {
        return sortDirection === 'asc'
          ? a.host.localeCompare(b.host)
          : b.host.localeCompare(a.host);
      }
      if (sortBy === 'status') {
        return sortDirection === 'asc'
          ? a.status.localeCompare(b.status)
          : b.status.localeCompare(a.status);
      }
      if (sortBy === 'latency') {
        return sortDirection === 'asc'
          ? a.latency - b.latency
          : b.latency - a.latency;
      }
      return 0;
    });

  // Pagination
  const totalPages = Math.ceil(filteredConnections.length / itemsPerPage);
  const paginatedConnections = filteredConnections.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  );

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mt-6">
      {/* Connection status indicator */}
      <div className="mb-4 flex items-center">
        <div className={`w-3 h-3 rounded-full mr-2 ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-sm text-gray-600">
          {connected ? 'Connected to server' : 'Disconnected'}
        </span>
        {error && <span className="text-sm text-red-500 ml-4">{error}</span>}
      </div>

      {/* Search and sort controls */}
      <div className="mb-4 flex items-center gap-4">
        <input
          type="text"
          placeholder="Search connections..."
          className="px-3 py-2 border rounded-md"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'host' | 'status' | 'latency')}
          className="px-3 py-2 border rounded-md"
        >
          <option value="host">Sort by Host</option>
          <option value="status">Sort by Status</option>
          <option value="latency">Sort by Latency</option>
        </select>
        <button
          onClick={() => setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')}
          className="px-3 py-2 border rounded-md"
        >
          {sortDirection === 'asc' ? '↑' : '↓'}
        </button>
      </div>

      {/* Connection list */}
      <div className="mt-4">
        {paginatedConnections.map((connection) => (
          <div
            key={`${connection.host}:${connection.port}`}
            className="border-b py-3 flex justify-between items-center hover:bg-gray-50"
          >
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {connection.host}:{connection.port}
                {blockedIPs.has(connection.host) && (
                  <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                    Blocked
                  </span>
                )}
              </div>
              <div className="text-sm text-gray-600">
                {connection.protocol} | {getProcessDisplay(connection)}
              </div>
              <div className="text-sm text-gray-500">
                Sent: {formatBytes(connection.bytesSent)} | 
                Received: {formatBytes(connection.bytesReceived)} | 
                Latency: {connection.latency}ms
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className={`px-2 py-1 rounded-md text-sm ${
                connection.status === 'SAFE' ? 'bg-green-100 text-green-800' :
                connection.status === 'SUSPICIOUS' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {connection.status}
              </span>
              {blockedIPs.has(connection.host) ? (
                <button
                  onClick={() => handleUnblock(connection)}
                  className="p-1 rounded hover:bg-green-100 transition-colors"
                  title="Unblock Connection"
                >
                  <Unlock className="w-4 h-4 text-green-600" />
                </button>
              ) : (
                <button
                  onClick={() => handleBlock(connection)}
                  className="p-1 rounded hover:bg-red-100 transition-colors"
                  title="Block Connection"
                >
                  <Lock className="w-4 h-4 text-red-600" />
                </button>
              )}
              <button
                onClick={() => setSelectedConnection(connection)}
                className="p-1 rounded hover:bg-gray-200 transition-colors"
                title="View Details"
              >
                <Database className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination controls */}
      <div className="mt-4 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Showing {((page - 1) * itemsPerPage) + 1} to {Math.min(page * itemsPerPage, filteredConnections.length)} of {filteredConnections.length}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 border rounded-md disabled:opacity-50 hover:bg-gray-50 transition-colors"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 border rounded-md disabled:opacity-50 hover:bg-gray-50 transition-colors"
          >
            Next
          </button>
        </div>
      </div>

      {/* Connection details modal */}
      {selectedConnection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg max-w-lg w-full">
            <h3 className="text-lg font-medium mb-4">Connection Details</h3>
            
            <div className="space-y-2">
              <DetailItem label="Host" value={selectedConnection.host} />
              <DetailItem label="Port" value={selectedConnection.port.toString()} />
              <DetailItem label="Protocol" value={selectedConnection.protocol} />
              <DetailItem label="Process" value={getProcessDisplay(selectedConnection)} />
              
              {selectedConnection.processInfo?.path && (
                <DetailItem label="Process Path" value={selectedConnection.processInfo.path} />
              )}
              
              {selectedConnection.processInfo?.cpu_percent !== undefined && (
                <DetailItem 
                  label="CPU Usage" 
                  value={`${selectedConnection.processInfo.cpu_percent.toFixed(1)}%`} 
                />
              )}
              
              {selectedConnection.processInfo?.memory_percent !== undefined && (
                <DetailItem 
                  label="Memory Usage" 
                  value={`${selectedConnection.processInfo.memory_percent.toFixed(1)}%`} 
                />
              )}
              
              <DetailItem label="Status" value={selectedConnection.status} />
              <DetailItem label="Bytes Sent" value={formatBytes(selectedConnection.bytesSent)} />
              <DetailItem label="Bytes Received" value={formatBytes(selectedConnection.bytesReceived)} />
              <DetailItem label="Latency" value={`${selectedConnection.latency}ms`} />
              
              {selectedConnection.last_seen && (
                <DetailItem 
                  label="Last Seen" 
                  value={new Date(selectedConnection.last_seen).toLocaleString()} 
                />
              )}
            </div>

            <div className="mt-6 flex gap-3">
              {blockedIPs.has(selectedConnection.host) ? (
                <button
                  onClick={() => handleUnblock(selectedConnection)}
                  className="px-4 py-2 bg-green-100 text-green-800 rounded-md hover:bg-green-200 transition-colors flex items-center justify-center gap-2 flex-1"
                >
                  <Unlock className="w-4 h-4" />
                  Unblock Connection
                </button>
              ) : (
                <button
                  onClick={() => handleBlock(selectedConnection)}
                  className="px-4 py-2 bg-red-100 text-red-800 rounded-md hover:bg-red-200 transition-colors flex items-center justify-center gap-2 flex-1"
                >
                  <Lock className="w-4 h-4" />
                  Block Connection
                </button>
              )}
              <button
                onClick={() => setSelectedConnection(null)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors flex-1"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const DetailItem: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex justify-between items-center text-sm p-2 bg-gray-50 rounded-md">
    <span className="text-gray-500">{label}:</span>
    <span className="font-medium">{value}</span>
  </div>
);