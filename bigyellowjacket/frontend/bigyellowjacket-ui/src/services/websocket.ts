import { create } from 'zustand';

interface WebSocketStore {
  socket: WebSocket | null;
  connected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  send: (message: any) => void;
}

export const useWebSocket = create<WebSocketStore>((set, get) => ({
  socket: null,
  connected: false,
  error: null,

  connect: () => {
    try {
      // Close existing socket if any
      const currentSocket = get().socket;
      if (currentSocket) {
        currentSocket.close();
      }

      const socket = new WebSocket('ws://localhost:8765');

      socket.onopen = () => {
        set({ connected: true, socket, error: null });
        console.log('Connected to server');
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Handle different message types
          switch (data.message_type) {
            case 'welcome':
              console.log('Received welcome message:', data.data.message);
              break;
            case 'error':
              console.error('Server error:', data.error);
              set({ error: data.error });
              break;
            case 'metrics_update':
              // Handle metrics update
              break;
            case 'connections_update':
              // Handle connections update
              break;
            default:
              console.log('Received message:', data);
          }
        } catch (e) {
          console.error('Error parsing message:', e);
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        set({ error: 'Connection error occurred' });
      };

      socket.onclose = () => {
        console.log('Disconnected from server');
        set({ connected: false, socket: null });
        
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          console.log('Attempting to reconnect...');
          get().connect();
        }, 5000);
      };

      set({ socket });
    } catch (e) {
      console.error('Connection error:', e);
      set({ error: 'Failed to connect to server', connected: false });
      
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        console.log('Attempting to reconnect...');
        get().connect();
      }, 5000);
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
      } catch (e) {
        console.error('Error sending message:', e);
        set({ error: 'Failed to send message' });
      }
    } else {
      set({ error: 'Not connected to server' });
      // Attempt to reconnect if socket is closed
      if (!socket || socket.readyState === WebSocket.CLOSED) {
        get().connect();
      }
    }
  },
}));

// Usage example:
/*
import { useWebSocket } from './websocket';

const MyComponent = () => {
  const { connected, error, connect, disconnect, send } = useWebSocket();

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return (
    <div>
      <div>Connection status: {connected ? 'Connected' : 'Disconnected'}</div>
      {error && <div>Error: {error}</div>}
      <button onClick={() => send({ type: 'ping' })}>Send Ping</button>
    </div>
  );
};
*/