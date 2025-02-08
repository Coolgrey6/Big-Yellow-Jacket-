// src/hooks/useWebSocket.ts

import { create } from 'zustand';
import { useEffect } from 'react';

// Interfaces
interface SystemMetrics {
  cpu: {
    percent: number;
    cores: number;
    frequency: number;
  };
  memory: {
    total: number;
    used: number;
    percent: number;
  };
  disk: {
    total: number;
    used: number;
    percent: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
  };
}

interface ConnectionMetrics {
  active: number;
  blocked: number;
  suspicious: number;
  safe: number;
}

interface TrafficMetrics {
  bytes_monitored: number;
}

interface Connection {
  host: string;
  port: number;
  protocol: string;
  process?: string;
  status: string;
  bytes_sent: number;
  bytes_received: number;
  latency: number;
  last_seen?: string;
  process_info?: {
    name: string;
    path: string;
  };
}

interface Alert {
  timestamp: string;
  type: string;
  endpoint: {
    host: string;
    port: number;
  };
  details: {
    count?: number;
    [key: string]: any;
  };
}

interface Metrics {
  system: SystemMetrics;
  connections: ConnectionMetrics;
  traffic: TrafficMetrics;
  timestamp?: string;
}

interface WebSocketState {
  socket: WebSocket | null;
  connected: boolean;
  error: string | null;
  metrics: Metrics;
  connections: Connection[];
  alerts: Alert[];
}

interface WebSocketActions {
  connect: () => void;
  disconnect: () => void;
  send: (message: any) => void;
  updateMetrics: (data: Partial<Metrics>) => void;
  updateConnections: (data: Connection[]) => void;
  updateAlerts: (data: Alert[]) => void;
}

const INITIAL_METRICS: Metrics = {
  system: {
    cpu: {
      percent: 0,
      cores: 0,
      frequency: 0
    },
    memory: {
      total: 0,
      used: 0,
      percent: 0
    },
    disk: {
      total: 0,
      used: 0,
      percent: 0
    },
    network: {
      bytes_sent: 0,
      bytes_recv: 0
    }
  },
  connections: {
    active: 0,
    blocked: 0,
    suspicious: 0,
    safe: 0
  },
  traffic: {
    bytes_monitored: 0
  }
};

const useWebSocketStore = create<WebSocketState & WebSocketActions>((set, get) => ({
  socket: null,
  connected: false,
  error: null,
  metrics: INITIAL_METRICS,
  connections: [],
  alerts: [],

  connect: () => {
    try {
      const socket = new WebSocket('ws://localhost:8765');

      socket.onopen = () => {
        set({ connected: true, error: null, socket });
        console.log('Connected to server');
        // Request initial data
        socket.send(JSON.stringify({ command: 'get_connections' }));
        socket.send(JSON.stringify({ command: 'get_alerts' }));
        socket.send(JSON.stringify({ command: 'get_metrics' }));
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.message_type) {
            case 'metrics_update':
              if (message.data) {
                const updatedMetrics = {
                  ...get().metrics,
                  ...message.data,
                  timestamp: new Date().toISOString()
                };
                set({ metrics: updatedMetrics });
              }
              break;
            case 'connections_update':
              if (message.data.active_connections) {
                const connections = Array.isArray(message.data.active_connections)
                  ? message.data.active_connections
                  : Object.values(message.data.active_connections);
                get().updateConnections(connections);
              }
              if (message.data.alerts) {
                get().updateAlerts(message.data.alerts);
              }
              break;
            case 'initial_state':
              if (message.data.metrics) {
                const initialMetrics = {
                  ...INITIAL_METRICS,
                  ...message.data.metrics,
                  timestamp: new Date().toISOString()
                };
                set({ metrics: initialMetrics });
              }
              if (message.data.active_connections) {
                const connections = Array.isArray(message.data.active_connections)
                  ? message.data.active_connections
                  : Object.values(message.data.active_connections);
                get().updateConnections(connections);
              }
              if (message.data.alerts) {
                get().updateAlerts(message.data.alerts);
              }
              break;
            case 'alert_update':
              if (message.data.alerts) {
                set(state => ({
                  alerts: [...message.data.alerts, ...state.alerts].slice(0, 10)
                }));
              }
              break;
            case 'error':
              console.error('Server error:', message.error);
              set({ error: message.error });
              break;
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        set({ error: 'Connection error occurred' });
      };

      socket.onclose = () => {
        console.log('Disconnected from server');
        set({ connected: false, socket: null });
      };

    } catch (error) {
      console.error('Connection error:', error);
      set({ error: 'Failed to connect to server', connected: false });
    }
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
      set({ socket: null, connected: false, error: null });
    }
  },

  send: (message: any) => {
    const { socket } = get();
    if (socket?.readyState === WebSocket.OPEN) {
      try {
        socket.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending message:', error);
        set({ error: 'Failed to send message' });
      }
    }
  },

  updateMetrics: (data) => set((state) => ({
    metrics: {
      ...state.metrics,
      ...data,
      timestamp: new Date().toISOString()
    }
  })),

  updateConnections: (data) => set({ connections: data }),

  updateAlerts: (data) => set({ alerts: data })
}));

export const useWebSocket = () => {
  const store = useWebSocketStore();
  
  useEffect(() => {
    store.connect();
    return () => store.disconnect();
  }, []);

  return store;
};

export { useWebSocketStore };