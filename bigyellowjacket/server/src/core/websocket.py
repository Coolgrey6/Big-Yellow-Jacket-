import asyncio
import json
import ssl
import websockets
import psutil
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Any, Optional
from src.utils.logger import logger
from src.models.datatypes import NetworkEndpoint
from config.settings import Config

import asyncio
import json
import websockets
import psutil
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Any
from src.utils.logger import logger

class WebSocketServer:
    def __init__(self, monitor, console):
        self.monitor = monitor
        self.console = console
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.output_dir = Path(Config.BASE_DIR) / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.running = False

    async def start(self):
        """Start the WebSocket server with metric broadcasting"""
        try:
            self.running = True
            
            # Start metric and connection broadcasting tasks
            broadcast_task = asyncio.create_task(self.start_metric_broadcast())
            connection_task = asyncio.create_task(self.start_connection_broadcast())
            
            async with websockets.serve(
                self.handle_client,
                host='localhost',
                port=8765,
                ping_interval=20,
                ping_timeout=60,  # Increased timeout
                max_size=2**23,
                compression=None  # Disable compression to reduce complexity
            ) as server:
                logger.info(f"WebSocket server started on ws://localhost:8765")
                
                while self.running:
                    try:
                        await asyncio.sleep(1)
                    except asyncio.CancelledError:
                        logger.info("Server shutdown initiated")
                        self.running = False
                        break
            
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.running = False
            raise
        finally:
            # Cleanup tasks
            if 'broadcast_task' in locals():
                broadcast_task.cancel()
            if 'connection_task' in locals():
                connection_task.cancel()
            
            # Close all client connections
            for client in self.clients.copy():
                await client.close()
            self.clients.clear()

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle client connection and messages"""
        try:
            # Add connection logging
            client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            logger.info(f"New client connected from {client_info}")
            
            await self.register(websocket)
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    # Removed path parameter from handle_command call
                    await self.handle_command(websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid message format from {client_info}: {message}")
                    await websocket.send(json.dumps({
                        'message_type': 'error',
                        'error': 'Invalid message format'
                    }))
                except Exception as e:
                    logger.error(f"Error handling message from {client_info}: {str(e)}")
                    await websocket.send(json.dumps({
                        'message_type': 'error',
                        'error': str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_info} connection closed normally")
        except Exception as e:
            logger.error(f"Error in client handler for {client_info}: {str(e)}")
        finally:
            await self.unregister(websocket)

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client registered. Total clients: {len(self.clients)}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            'message_type': 'welcome',
            'data': {
                'timestamp': datetime.now().isoformat(),
                'message': 'Connected to network monitoring server'
            }
        }))

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client connection"""
        self.clients.remove(websocket)
        # Clean up any metric streaming tasks
        if websocket in self.metric_tasks:
            self.metric_tasks[websocket].cancel()
            del self.metric_tasks[websocket]
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            disconnected = set()
            message_str = json.dumps(message)
            
            for client in self.clients:
                try:
                    await client.send(message_str)
                except websockets.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.add(client)
                    
            # Remove disconnected clients
            for client in disconnected:
                await self.unregister(client)

    async def send_initial_state(self, websocket: websockets.WebSocketServerProtocol):
        """Send initial state to new client"""
        try:
            # Get current system state
            connections = {
                key: endpoint.to_dict() 
                for key, endpoint in self.monitor.active_connections.items()
            }
            
            metrics = await self.gather_metrics()
            
            initial_state = {
                'message_type': 'initial_state',
                'data': {
                    'active_connections': connections,
                    'blocked_ips': list(self.monitor.blocked_ips),
                    'statistics': self.monitor.get_statistics(),
                    'metrics': metrics,
                    'alerts': self.monitor.alerts[-10:]  # Last 10 alerts
                }
            }
            
            await websocket.send(json.dumps(initial_state))
            
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")

    async def gather_metrics(self) -> Dict:
        """Gather real-time system metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network_io = psutil.net_io_counters()
            
            # Get monitor statistics
            stats = self.monitor.get_statistics()
            
            return {
                'system': {
                    'cpu': {
                        'percent': cpu_percent,
                        'cores': psutil.cpu_count(),
                        'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0
                    },
                    'memory': {
                        'total': memory.total,
                        'used': memory.used,
                        'percent': memory.percent
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'percent': disk.percent
                    },
                    'network': {
                        'bytes_sent': network_io.bytes_sent,
                        'bytes_recv': network_io.bytes_recv,
                        'packets_sent': network_io.packets_sent,
                        'packets_recv': network_io.packets_recv
                    }
                },
                'monitoring': {
                    'active_connections': stats['connections']['active'],
                    'total_connections': stats['connections']['total'],
                    'blocked_ips': len(self.monitor.blocked_ips),
                    'alerts': len(self.monitor.alerts),
                    'bytes_monitored': stats['traffic']['total_bytes_monitored']
                },
                'security': {
                    'suspicious_connections': stats['connections']['suspicious'],
                    'safe_connections': stats['connections']['safe'],
                    'recent_alerts': stats['security']['recent_alerts']
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error gathering metrics: {e}")
            return {}

    async def start(self):
        """Start the WebSocket server with metric broadcasting"""
        try:
            # Start metric and connection broadcasting tasks
            broadcast_task = asyncio.create_task(self.start_metric_broadcast())
            connection_task = asyncio.create_task(self.start_connection_broadcast())
            
            server = await websockets.serve(
                self.handle_client,
                Config.SERVER.HOST,
                Config.SERVER.PORT,
                ping_interval=20,
                ping_timeout=10,
                max_size=2**23  # 8MB max message size
            )
            
            logger.info(
                f"WebSocket server started on "
                f"ws://{Config.SERVER.HOST}:{Config.SERVER.PORT}"
            )
            
            try:
                await server.wait_closed()
            except asyncio.CancelledError:
                logger.info("WebSocket server shutdown initiated")
                broadcast_task.cancel()
                connection_task.cancel()
                try:
                    await broadcast_task
                    await connection_task
                except asyncio.CancelledError:
                    pass
                server.close()
                await server.wait_closed()
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

    async def start_metric_broadcast(self):
        """Broadcast metrics to all clients periodically"""
        while True:
            try:
                if self.clients:
                    # Get real-time system metrics
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory = psutil.virtual_memory()
                    net_io = psutil.net_io_counters()
                    connections = self.monitor.get_statistics()

                    metrics_data = {
                        'message_type': 'metrics_update',
                        'data': {
                            'system': {
                                'cpu': cpu_percent,
                                'memory': memory.percent,
                                'network': {
                                    'bytes_sent': net_io.bytes_sent,
                                    'bytes_recv': net_io.bytes_recv
                                }
                            },
                            'connections': {
                                'active': len(self.monitor.active_connections),
                                'blocked': len(self.monitor.blocked_ips),
                                'suspicious': connections.get('connections', {}).get('suspicious', 0),
                                'safe': connections.get('connections', {}).get('safe', 0)
                            },
                            'traffic': {
                                'bytes_monitored': connections.get('traffic', {}).get('total_bytes_monitored', 0)
                            }
                        },
                        'timestamp': datetime.now().isoformat()
                    }

                    await self.broadcast(metrics_data)

                await asyncio.sleep(1)  # Update every second
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error in metric broadcast: {e}")
                await asyncio.sleep(5)

    async def start_connection_broadcast(self):
        """Broadcast connection updates to all clients periodically"""
        while True:
            try:
                if self.clients:
                    active_connections = []
                    for conn in self.monitor.active_connections.values():
                        try:
                            connection_data = {
                                'host': conn.host,
                                'port': conn.port,
                                'protocol': conn.protocol,
                                'process': conn.process_info.name if conn.process_info else 'Unknown',
                                'status': conn.security_assessment.risk_level if conn.security_assessment else 'UNKNOWN',
                                'bytes_sent': conn.bytes_sent,
                                'bytes_received': conn.bytes_received,
                                'latency': conn.latency if hasattr(conn, 'latency') else 0,
                                'last_seen': conn.last_seen.isoformat() if conn.last_seen else None
                            }
                            active_connections.append(connection_data)
                        except Exception as e:
                            logger.error(f"Error processing connection data: {e}")

                    connection_update = {
                        'message_type': 'connections_update',
                        'data': {
                            'active_connections': active_connections,
                            'statistics': self.monitor.get_statistics(),
                            'alerts': [alert for alert in self.monitor.alerts[-5:]]  # Last 5 alerts
                        },
                        'timestamp': datetime.now().isoformat()
                    }

                    await self.broadcast(connection_update)

                await asyncio.sleep(1)  # Update every second
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error in connection broadcast: {e}")
                await asyncio.sleep(5)

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Handle client connection and messages"""
        try:
            await self.register(websocket)
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_command(websocket, path, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid message format: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed normally")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister(websocket)

    async def handle_command(self, websocket: websockets.WebSocketServerProtocol, data: Dict):
        """Handle client commands"""
        try:
            command = data.get('command')
            params = data.get('params', {})
            
            commands = {
                'block_ip': self.handle_block_ip,
                'unblock_ip': self.handle_unblock_ip,
                'block_inbound': self.handle_block_inbound,
                'block_outbound': self.handle_block_outbound,
                'unblock_inbound': self.handle_unblock_inbound,
                'unblock_outbound': self.handle_unblock_outbound,
                'get_connection_details': self.handle_connection_details,
                'export_data': self.handle_export_data
            }
            
            handler = commands.get(command)
            if handler:
                await handler(websocket, params)
            else:
                await websocket.send(json.dumps({
                    'message_type': 'error',
                    'error': f'Unknown command: {command}'
                }))
                
        except Exception as e:
            logger.error(f"Error handling command: {str(e)}")
            await websocket.send(json.dumps({
                'message_type': 'error',
                'error': str(e)
            }))

    async def handle_block_ip(self, websocket: websockets.WebSocketServerProtocol, params: Dict):
        """Handle IP blocking command"""
        host = params.get('host')
        if host:
            self.monitor.block_ip(host)
            await self.broadcast({
                'message_type': 'ip_blocked',
                'data': {'host': host}
            })

    async def handle_block_inbound(self, websocket: websockets.WebSocketServerProtocol, params: Dict):
        """Handle inbound traffic blocking command"""
        self.monitor.block_all_inbound()
        await self.broadcast({
            'message_type': 'inbound_blocked',
            'timestamp': datetime.now().isoformat()
        })

    async def handle_block_outbound(self, websocket: websockets.WebSocketServerProtocol, params: Dict):
        """Handle outbound traffic blocking command"""
        self.monitor.block_all_outbound()
        await self.broadcast({
            'message_type': 'outbound_blocked',
            'timestamp': datetime.now().isoformat()
        })

    async def handle_unblock_inbound(self, websocket: websockets.WebSocketServerProtocol, params: Dict):
        """Handle inbound traffic unblocking command"""
        self.monitor.unblock_all_inbound()
        await self.broadcast({
            'message_type': 'inbound_unblocked',
            'timestamp': datetime.now().isoformat()
        })

    async def handle_unblock_outbound(self, websocket: websockets.WebSocketServerProtocol, params: Dict):
        """Handle outbound traffic unblocking command"""
        self.monitor.unblock_all_outbound()
        await self.broadcast({
            'message_type': 'outbound_unblocked',
            'timestamp': datetime.now().isoformat()
        })

    async def handle_connection_details(self, websocket: websockets.WebSocketServerProtocol, params: Dict):
        """Handle connection details request"""
        host = params.get('host')
        port = params.get('port')
        if host and port:
            details = self.monitor.get_connection_details(host, port)
            await websocket.send(json.dumps({
                'message_type': 'connection_details',
                'data': details
            }))

    async def handle_export_data(self, websocket: websockets.WebSocketServerProtocol, params: Dict):
        """Handle data export request"""
        export_type = params.get('type', 'all')
        format_type = params.get('format', 'json')
        result = await self.monitor.export_data(export_type, format_type)
        await websocket.send(json.dumps({
            'message_type': 'export_complete',
            'data': result
        }))