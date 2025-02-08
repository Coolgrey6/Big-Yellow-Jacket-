import asyncio
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from pathlib import Path
import json
import socket
import time
import aiofiles  # Add this line
from src.utils.logger import logger
from src.models.datatypes import NetworkEndpoint, ProcessInfo
from src.analyzers.intelligence import NetworkIntelligenceGatherer

class NetworkMonitor:
    """Core network monitoring system"""
    
    def __init__(self, console_monitor):
        self.console = console_monitor
        self.active_connections: Dict[str, NetworkEndpoint] = {}
        self.blocked_ips: Set[str] = set()
        self.alerts = []
        self.intelligence_gatherer = NetworkIntelligenceGatherer(console_monitor)
        self.connection_history: Dict[str, Dict] = {}
        self.last_check = 0
        self.check_interval = 2  # seconds
        
        # Initialize tracking variables
        self.inbound_blocked = False
        self.outbound_blocked = False
        self.monitoring_enabled = True
        self.alert_count = 0
        self.total_bytes_monitored = 0
        
        # Statistics tracking
        self.last_stats = None
        self.last_stats_time = datetime.now()
        self.hourly_stats = []
        self.daily_stats = []
        
        # Load previously blocked IPs
        self.load_blocked_ips()
        
        # Create required directories
        self.setup_directories()
        
    # Rest of the code remains the same
        
    def setup_directories(self):
        """Create required directories"""
        directories = ['data', 'data/alerts', 'data/exports', 'data/stats', 'logs']
        for dir_name in directories:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
            
    def load_blocked_ips(self):
        """Load previously blocked IPs from file"""
        try:
            blocked_file = Path("data/blocked_ips.txt")
            if blocked_file.exists():
                with open(blocked_file) as f:
                    self.blocked_ips.update(
                        line.strip() for line in f
                        if line.strip() and not line.startswith('#')
                    )
                logger.info(f"Loaded {len(self.blocked_ips)} blocked IPs")
        except Exception as e:
            logger.error(f"Error loading blocked IPs: {e}")
            
    def save_blocked_ips(self):
        """Save blocked IPs to file"""
        try:
            blocked_file = Path("data/blocked_ips.txt")
            with open(blocked_file, 'w') as f:
                for ip in sorted(self.blocked_ips):
                    f.write(f"{ip}\n")
        except Exception as e:
            logger.error(f"Error saving blocked IPs: {e}")
            
    async def get_process_connections(self) -> List[NetworkEndpoint]:
        """Get all active network connections"""
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                try:
                    if (conn.status == psutil.CONN_ESTABLISHED and 
                        conn.raddr and 
                        conn.raddr.ip and 
                        not conn.raddr.ip.startswith(('127.', '192.168.', '10.', '172.16.'))):
                        
                        try:
                            process = psutil.Process(conn.pid)
                            process_info = ProcessInfo(
                                pid=conn.pid,
                                name=process.name(),
                                path=process.exe(),
                                command_line=' '.join(process.cmdline()),
                                username=process.username(),
                                creation_time=datetime.fromtimestamp(process.create_time()),
                                cpu_percent=process.cpu_percent(),
                                memory_percent=process.memory_percent(),
                                status=process.status()
                            )
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_info = None

                        # Create endpoint
                        endpoint = NetworkEndpoint(
                            host=conn.raddr.ip,
                            port=conn.raddr.port,
                            protocol='TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                            connection_state=conn.status,
                            last_seen=datetime.now(),
                            process_info=process_info
                        )
                        
                        connections.append(endpoint)
                        
                except Exception as e:
                    logger.debug(f"Error processing connection: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting connections: {e}")
            
        return connections

    async def process_connections(self, connections: List[NetworkEndpoint]):
        """Process list of connections concurrently"""
        tasks = []
        for endpoint in connections:
            if endpoint.host not in self.blocked_ips:
                if not self.inbound_blocked or not self.is_inbound(endpoint):
                    if not self.outbound_blocked or not self.is_outbound(endpoint):
                        task = asyncio.create_task(
                            self.intelligence_gatherer.gather_intelligence(endpoint)
                        )
                        tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for endpoint in results:
                if isinstance(endpoint, NetworkEndpoint):
                    await self.update_connection_status(endpoint)
                elif isinstance(endpoint, Exception):
                    logger.error(f"Error processing connection: {endpoint}")

    async def update_statistics(self):
            """Update real-time statistics"""
            try:
                current_time = datetime.now()
                current_stats = self.get_statistics()

                # Update historical trends
                if not hasattr(self, '_previous_stats'):
                    self._previous_stats = current_stats
                    self._previous_stats_time = current_time
                    return

                # Calculate time difference
                time_diff = (current_time - self._previous_stats_time).total_seconds()
                if time_diff > 0:
                    try:
                        # Calculate connection rate
                        connection_change = (
                            current_stats["connections"]["active"] - 
                            self._previous_stats["connections"]["active"]
                        )
                        
                        # Calculate traffic rate
                        traffic_change = (
                            current_stats["traffic"]["total_bytes_monitored"] - 
                            self._previous_stats["traffic"]["total_bytes_monitored"]
                        )
                        
                        # Calculate alert rate
                        alert_change = (
                            current_stats["security"]["total_alerts"] - 
                            self._previous_stats["security"]["total_alerts"]
                        )

                        # Store rates
                        self._rates = {
                            "connections_per_second": connection_change / time_diff,
                            "bytes_per_second": traffic_change / time_diff,
                            "alerts_per_second": alert_change / time_diff
                        }
                    except KeyError:
                        # Handle missing keys in previous stats
                        self._rates = {
                            "connections_per_second": 0,
                            "bytes_per_second": 0,
                            "alerts_per_second": 0
                        }

                # Update previous stats
                self._previous_stats = current_stats
                self._previous_stats_time = current_time

                # Save current stats to historical data
                self.update_historical_stats()

            except Exception as e:
                logger.error(f"Error updating statistics: {e}")

            @property
            def current_rates(self) -> dict:
                """Get current rates"""
                if not hasattr(self, '_rates'):
                    self._rates = {
                        "connections_per_second": 0,
                        "bytes_per_second": 0,
                        "alerts_per_second": 0
                    }
                return self._rates

    async def start_monitoring(self):
        """Start network monitoring"""
        logger.info("Starting network monitoring...")
        
        while True:
            try:
                if not self.monitoring_enabled:
                    await asyncio.sleep(1)
                    continue
                    
                current_time = time.time()
                if current_time - self.last_check >= self.check_interval:
                    # Get current connections
                    connections = await self.get_process_connections()
                    
                    # Process connections concurrently
                    await self.process_connections(connections)
                    
                    self.last_check = current_time
                    
                    # Cleanup and maintenance
                    await self.perform_maintenance()
                    
                    # Update statistics
                    await self.update_statistics()
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
                
    async def perform_maintenance(self):
        """Perform regular maintenance tasks"""
        try:
            # Cleanup old connections
            self.cleanup_old_connections()
            
            # Archive old alerts
            await self.archive_old_alerts()
            
            # Update historical statistics
            self.update_historical_stats()
            
        except Exception as e:
            logger.error(f"Error in maintenance: {e}")

    async def archive_old_alerts(self):
        """Archive alerts older than 24 hours"""
        try:
            current_time = datetime.now()
            old_alerts = []
            
            for alert in self.alerts[:]:
                alert_time = datetime.fromisoformat(alert['timestamp'])
                if (current_time - alert_time) > timedelta(hours=24):
                    old_alerts.append(alert)
                    self.alerts.remove(alert)
            
            if old_alerts:
                archive_file = Path(f"data/alerts/archive_{current_time.strftime('%Y%m%d')}.json")
                with open(archive_file, 'a') as f:
                    for alert in old_alerts:
                        f.write(json.dumps(alert) + '\n')
                        
        except Exception as e:
            logger.error(f"Error archiving alerts: {e}")

    def update_historical_stats(self):
        """Update historical statistics"""
        try:
            current_time = datetime.now()
            current_stats = self.get_statistics()
            
            # Update hourly stats
            if not self.hourly_stats or (current_time - self.hourly_stats[-1]['timestamp'] > timedelta(hours=1)):
                self.hourly_stats.append({
                    'timestamp': current_time,
                    'stats': current_stats
                })
                # Keep last 24 hours
                if len(self.hourly_stats) > 24:
                    self.hourly_stats.pop(0)
            
            # Update daily stats
            if not self.daily_stats or (current_time - self.daily_stats[-1]['timestamp'] > timedelta(days=1)):
                self.daily_stats.append({
                    'timestamp': current_time,
                    'stats': current_stats
                })
                # Keep last 30 days
                if len(self.daily_stats) > 30:
                    self.daily_stats.pop(0)
                    
            # Save historical stats
            self.save_historical_stats()
            
        except Exception as e:
            logger.error(f"Error updating historical stats: {e}")

    def save_historical_stats(self):
        """Save historical statistics to file"""
        try:
            stats_file = Path("data/stats/historical_stats.json")
            with open(stats_file, 'w') as f:
                json.dump({
                    'hourly': self.hourly_stats,
                    'daily': self.daily_stats
                }, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving historical stats: {e}")
                
    async def update_connection_status(self, endpoint: NetworkEndpoint):
        """Update connection status and check for suspicious activity"""
        key = f"{endpoint.host}:{endpoint.port}"
        
        # Check if this is a new connection
        is_new = key not in self.active_connections
        
        if is_new:
            # Check for rapid connections from this IP
            recent_connections = sum(
                1 for conn in self.active_connections.values()
                if conn.host == endpoint.host and 
                (datetime.now() - conn.last_seen).total_seconds() < 60
            )
            
            if recent_connections > 3:
                await self.add_alert(
                    'rapid_reconnection',
                    endpoint,
                    {'count': recent_connections}
                )
        
        # Update connection record
        self.active_connections[key] = endpoint
        
        # Update history
        self.update_history(endpoint)
        
        # Update metrics
        self.total_bytes_monitored += (endpoint.bytes_sent + endpoint.bytes_received)
        
        # Update console
        self.console.update_endpoint(endpoint)
        
    def is_inbound(self, endpoint: NetworkEndpoint) -> bool:
        """Determine if connection is inbound"""
        try:
            # Check if the remote port is a well-known service port
            return endpoint.port < 1024
        except Exception as e:
            logger.error(f"Error checking inbound status: {e}")
            return False
            
    def is_outbound(self, endpoint: NetworkEndpoint) -> bool:
        """Determine if connection is outbound"""
        return not self.is_inbound(endpoint)
        
    def update_history(self, endpoint: NetworkEndpoint):
        """Update connection history"""
        key = f"{endpoint.host}:{endpoint.port}"
        
        if key not in self.connection_history:
            self.connection_history[key] = {
                'first_seen': datetime.now(),
                'connection_count': 1,
                'total_bytes_sent': 0,
                'total_bytes_received': 0,
                'risk_levels': [],
                'alerts': []
            }
        
        history = self.connection_history[key]
        history['connection_count'] += 1
        history['total_bytes_sent'] += endpoint.bytes_sent
        history['total_bytes_received'] += endpoint.bytes_received
        
        if endpoint.security_assessment:
            history['risk_levels'].append({
                'timestamp': datetime.now().isoformat(),
                'level': endpoint.security_assessment.risk_level
            })
            
    async def add_alert(self, alert_type: str, endpoint: NetworkEndpoint, details: dict):
        """Add a new security alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'endpoint': endpoint.to_dict(),
            'details': details
        }
        
        self.alerts.append(alert)
        self.alert_count += 1
        self.console.add_alert(alert)
        
        # Save alert to file
        await self.save_alert(alert)
        
        # Update connection history
        key = f"{endpoint.host}:{endpoint.port}"
        if key in self.connection_history:
            self.connection_history[key]['alerts'].append(alert)
        
    async def save_alert(self, alert: dict):
        """Save alert to file"""
        try:
            alert_dir = Path("data/alerts")
            alert_file = alert_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            async with aiofiles.open(alert_file, 'w') as f:
                await f.write(json.dumps(alert, indent=2))
                
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
            
    def cleanup_old_connections(self):
        """Remove old connections"""
        current_time = datetime.now()
        to_remove = []
        
        for key, endpoint in self.active_connections.items():
            if (current_time - endpoint.last_seen).total_seconds() > 300:  # 5 minutes
                to_remove.append(key)
                
        for key in to_remove:
            del self.active_connections[key]
            
    def get_statistics(self) -> dict:
        """Get current monitoring statistics"""
        try:
            current_time = datetime.now()
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            
            stats = {
                # System metrics
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used": memory.used,
                    "memory_total": memory.total,
                    "disk_percent": disk.percent,
                    "network_bytes_sent": net_io.bytes_sent,
                    "network_bytes_recv": net_io.bytes_recv
                },
                
                # Connection metrics
                "connections": {
                    "active": len(self.active_connections),
                    "total": len(self.connection_history),
                    "blocked": len(self.blocked_ips),
                    "suspicious": sum(
                        1 for conn in self.active_connections.values()
                        if conn.security_assessment and conn.security_assessment.risk_level != "LOW"
                    ),
                    "safe": sum(
                        1 for conn in self.active_connections.values()
                        if conn.security_assessment and conn.security_assessment.risk_level == "LOW"
                    )
                },
                
                # Traffic metrics
                "traffic": {
                    "total_bytes_monitored": self.total_bytes_monitored,
                    "bytes_sent": sum(conn.bytes_sent for conn in self.active_connections.values()),
                    "bytes_received": sum(conn.bytes_received for conn in self.active_connections.values())
                },
                
# Security metrics
                "security": {
                    "total_alerts": self.alert_count,
                    "recent_alerts": len([
                        alert for alert in self.alerts
                        if (current_time - datetime.fromisoformat(alert['timestamp'])).total_seconds() < 3600
                    ]),
                    "blocked_ips": len(self.blocked_ips),
                    "inbound_blocked": self.inbound_blocked,
                    "outbound_blocked": self.outbound_blocked
                },
                
                # Process metrics
                "processes": {
                    "total": len(set(
                        conn.process_info.pid for conn in self.active_connections.values()
                        if conn.process_info and conn.process_info.pid
                    )),
                    "types": len(set(
                        conn.process_info.name for conn in self.active_connections.values()
                        if conn.process_info and conn.process_info.name
                    ))
                },
                
                # Status flags
                "status": {
                    "monitoring_enabled": self.monitoring_enabled,
                    "last_check": self.last_check,
                    "check_interval": self.check_interval
                },
                
                # Timestamp
                "timestamp": current_time.isoformat()
            }
            
            # Calculate trends if we have previous stats
            if self.last_stats:
                time_diff = (current_time - self.last_stats_time).total_seconds()
                if time_diff > 0:
                    stats["trends"] = {
                        "connections": {
                            "change": stats["connections"]["active"] - self.last_stats["connections"]["active"],
                            "change_rate": (stats["connections"]["active"] - self.last_stats["connections"]["active"]) / time_diff
                        },
                        "traffic": {
                            "bytes_change": stats["traffic"]["total_bytes_monitored"] - self.last_stats["traffic"]["total_bytes_monitored"],
                            "bytes_rate": (stats["traffic"]["total_bytes_monitored"] - self.last_stats["traffic"]["total_bytes_monitored"]) / time_diff
                        },
                        "security": {
                            "alerts_change": stats["security"]["total_alerts"] - self.last_stats["security"]["total_alerts"],
                            "alerts_rate": (stats["security"]["total_alerts"] - self.last_stats["security"]["total_alerts"]) / time_diff
                        }
                    }
            
            # Store current stats for next trend calculation
            self.last_stats = stats.copy()
            self.last_stats_time = current_time
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def block_ip(self, host: str):
        """Block an IP address"""
        try:
            self.blocked_ips.add(host)
            self.save_blocked_ips()
            
            # Close any active connections
            for key in list(self.active_connections.keys()):
                if self.active_connections[key].host == host:
                    del self.active_connections[key]
                    
            # Update console
            self.console.increment_blocked()
            logger.info(f"Blocked IP: {host}")
            
            # Add block event to history
            self.add_block_event(host)
            
        except Exception as e:
            logger.error(f"Error blocking IP {host}: {e}")

    def add_block_event(self, host: str):
        """Record IP block event"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "ip": host,
                "reason": "Manual block",
                "active_connections": [
                    conn.to_dict() for conn in self.active_connections.values()
                    if conn.host == host
                ]
            }
            
            block_file = Path("data/blocked_events.json")
            events = []
            
            if block_file.exists():
                with open(block_file) as f:
                    events = json.load(f)
                    
            events.append(event)
            
            with open(block_file, 'w') as f:
                json.dump(events, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error recording block event: {e}")
                
    def unblock_ip(self, host: str):
        """Unblock an IP address"""
        try:
            self.blocked_ips.discard(host)
            self.save_blocked_ips()
            logger.info(f"Unblocked IP: {host}")
            
        except Exception as e:
            logger.error(f"Error unblocking IP {host}: {e}")
            
    def block_all_inbound(self):
        """Block all inbound connections"""
        self.inbound_blocked = True
        logger.info("Blocked all inbound connections")
        
    def block_all_outbound(self):
        """Block all outbound connections"""
        self.outbound_blocked = True
        logger.info("Blocked all outbound connections")
        
    def unblock_all_inbound(self):
        """Unblock all inbound connections"""
        self.inbound_blocked = False
        logger.info("Unblocked all inbound connections")
        
    def unblock_all_outbound(self):
        """Unblock all outbound connections"""
        self.outbound_blocked = False
        logger.info("Unblocked all outbound connections")
        
    def get_connection_details(self, host: str, port: int) -> Optional[Dict]:
        """Get detailed information about a specific connection"""
        key = f"{host}:{port}"
        endpoint = self.active_connections.get(key)
        
        if endpoint:
            history = self.connection_history.get(key, {})
            
            return {
                "connection": endpoint.to_dict(),
                "history": {
                    "first_seen": history.get("first_seen"),
                    "connection_count": history.get("connection_count", 0),
                    "total_bytes_sent": history.get("total_bytes_sent", 0),
                    "total_bytes_received": history.get("total_bytes_received", 0),
                    "risk_history": history.get("risk_levels", []),
                    "alerts": history.get("alerts", [])
                }
            }
            
        return None
        
    async def export_data(self, export_type: str = 'all', format_type: str = 'json') -> dict:
        """Export monitoring data"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'active_connections': {},
                'connection_history': {},
                'blocked_ips': list(self.blocked_ips),
                'alerts': self.alerts[-1000:],  # Last 1000 alerts
                'statistics': self.get_statistics()
            }
            
            if export_type in ['all', 'connections']:
                export_data['active_connections'] = {
                    key: endpoint.to_dict() 
                    for key, endpoint in self.active_connections.items()
                }
                
            if export_type in ['all', 'history']:
                export_data['connection_history'] = self.connection_history
                
            # Save export
            export_dir = Path("data/exports")
            file_path = export_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
            return {
                'file': str(file_path),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }