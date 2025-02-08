import { useEffect, useRef, useState } from 'react';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState({});
  const [connections, setConnections] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Create a new WebSocket connection
    ws.current = new WebSocket('wss://localhost:8000');

    // Handle connection opened
    ws.current.onopen = () => {
      console.log('WebSocket connection opened');
      setIsConnected(true);
    };

    // Handle messages received
    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      switch (message.message_type) {
        case 'metrics_update':
          setMetrics(message.data);
          break;
        case 'connections_update':
          setConnections(message.data.active_connections);
          setAlerts(message.data.alerts);
          break;
        default:
          console.log('Unknown message type:', message.message_type);
      }
    };

    // Handle connection closed
    ws.current.onclose = () => {
      console.log('WebSocket connection closed');
      setIsConnected(false);
    };

    // Clean up the WebSocket connection on component unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  return {
    isConnected,
    metrics,
    connections,
    alerts,
    sendMessage: (message: any) => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify(message));
      }
    },
  };
};