import asyncio
import os
import sys
from datetime import datetime
import psutil
from colorama import Fore, Style
from src.models.datatypes import NetworkEndpoint
from src.utils.logger import logger
from typing import Dict, List

class ConsoleMonitor:
    """Real-time console display for network monitoring"""
    
    def __init__(self, enable_console: bool = True):
        self.enable_console = enable_console
        self.endpoints: Dict[str, NetworkEndpoint] = {}
        self.start_time = datetime.now()
        self.total_connections = 0
        self.blocked_count = 0
        self.alert_count = 0
        self.last_update = datetime.now()
        self.refresh_rate = 1
        self.recent_alerts = []
        self.max_recent_alerts = 5
        self.running = True

    async def start_updates(self):
        """Start the console update loop"""
        logger.info("Starting console updates...")
        while self.running:
            try:
                if self.enable_console:
                    self.print_status()
                await asyncio.sleep(self.refresh_rate)
            except Exception as e:
                logger.error(f"Error in console update: {e}")
                await asyncio.sleep(1)

    def stop_updates(self):
        """Stop the console update loop"""
        self.running = False
        logger.info("Stopping console updates...")

    def clear_screen(self):
        """Clear the console screen"""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')

    def print_status(self):
        """Print complete status display"""
        if not self.enable_console:
            return

        if (datetime.now() - self.last_update).total_seconds() < self.refresh_rate:
            return

        self.last_update = datetime.now()
        self.clear_screen()
        self.print_header()
        self.print_system_status()
        self.print_active_connections()
        self.print_alerts()
        self.print_performance()

    def print_header(self):
        """Print the application header"""
        print(f"{Fore.YELLOW}")
        print("=" * 100)
        print("""
    ____  _       __   __ _ _                 _            _        __ 
   / __ )(_)__ _ / /  / /(_) /__ ___ _    __/ /__ ____  (_)__ ___/ /_
  / __  / //  ' / _ \/ // /  ' \/ _ `/ |/|/ / / -_) __/ / / // _  / -_)
 /_/ /_/_//_/_/_.__/_//_/_/_/_/\_,_/|__,__/_/\__/_/ __/ /\_,_/_,_/\__/ 
                              Security Monitor v2.0
        """)
        print("=" * 100)
        print(f"{Style.RESET_ALL}")

    def print_system_status(self):
        """Print system status section"""
        uptime = datetime.now() - self.start_time
        print(f"\n{Fore.CYAN}█ System Status {Style.RESET_ALL}")
        print(f"├─ Uptime: {str(uptime).split('.')[0]}")
        print(f"├─ Total Connections: {self.total_connections}")
        print(f"├─ Active Endpoints: {len(self.endpoints)}")
        print(f"├─ Blocked IPs: {self.blocked_count}")
        print(f"└─ Security Alerts: {self.alert_count}")

    def print_active_connections(self):
        """Print active connections section"""
        print(f"\n{Fore.CYAN}█ Active Connections {Style.RESET_ALL}")
        if not self.endpoints:
            print("└─ No active connections")
            return

        print("┌" + "─" * 98 + "┐")
        print(f"│ {'IP Address':<20} {'Port':<8} {'Status':<12} {'Process':<15} {'Type':<12} {'Latency':<10} │")
        print("├" + "─" * 98 + "┤")
        
        for endpoint in self.endpoints.values():
            status_color = Fore.GREEN if endpoint.is_safe else Fore.RED
            status = "SAFE" if endpoint.is_safe else "SUSPICIOUS"
            latency = f"{endpoint.latency:.1f}ms" if endpoint.latency else "N/A"
            process = endpoint.process_info.name if endpoint.process_info else "Unknown"
            device_type = endpoint.device_type or "Unknown"
            
            print(f"│ {status_color}{endpoint.host:<20}{Style.RESET_ALL} "
                  f"{endpoint.port:<8} "
                  f"{status_color}{status:<12}{Style.RESET_ALL} "
                  f"{process:<15} "
                  f"{device_type:<12} "
                  f"{latency:<10} │")

        print("└" + "─" * 98 + "┘")

    def print_alerts(self):
        """Print recent alerts section"""
        if self.recent_alerts:
            print(f"\n{Fore.CYAN}█ Recent Alerts {Style.RESET_ALL}")
            print("┌" + "─" * 98 + "┐")
            for alert in self.recent_alerts[-5:]:
                alert_time = datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')
                print(f"│ {Fore.RED}[{alert_time}] {alert['type']}: {alert['details'][:80]}{Style.RESET_ALL}")
            print("└" + "─" * 98 + "┘")

    def print_performance(self):
        """Print system performance section"""
        print(f"\n{Fore.CYAN}█ System Performance {Style.RESET_ALL}")
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        print(f"├─ CPU Usage: {self.get_progress_bar(cpu_percent)} {cpu_percent}%")
        print(f"└─ Memory Usage: {self.get_progress_bar(memory.percent)} {memory.percent}%")

    def get_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Generate a colored progress bar"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        if percentage < 60:
            return f"{Fore.GREEN}{bar}{Style.RESET_ALL}"
        elif percentage < 80:
            return f"{Fore.YELLOW}{bar}{Style.RESET_ALL}"
        else:
            return f"{Fore.RED}{bar}{Style.RESET_ALL}"

    def update_endpoint(self, endpoint: NetworkEndpoint):
        """Update endpoint information"""
        key = f"{endpoint.host}:{endpoint.port}"
        if key not in self.endpoints:
            endpoint.first_seen = datetime.now()
            endpoint.connection_count = 1
            self.total_connections += 1
        else:
            endpoint.connection_count = self.endpoints[key].connection_count + 1
            endpoint.first_seen = self.endpoints[key].first_seen
        
        endpoint.last_seen = datetime.now()
        self.endpoints[key] = endpoint
        
        if not endpoint.is_safe and self.enable_console:
            logger.warning(f"Suspicious connection detected: {endpoint.host}:{endpoint.port}")
            self.alert_count += 1

    def remove_endpoint(self, host: str, port: int):
        """Remove an endpoint from tracking"""
        key = f"{host}:{port}"
        if key in self.endpoints:
            del self.endpoints[key]

    def increment_blocked(self):
        """Increment blocked connections counter"""
        self.blocked_count += 1

    @staticmethod
    def format_bytes(bytes_val: int) -> str:
        """Format bytes into human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f}TB"
    
    def add_alert(self, alert: dict):
        try:
            # Format the alert if needed
            if isinstance(alert, dict):
                if 'details' in alert and isinstance(alert['details'], dict):
                    # Convert dict details to string
                    details_str = ', '.join(f"{k}: {v}" for k, v in alert['details'].items())
                    alert = {
                        **alert,
                        'details': details_str
                    }

            # Add to recent alerts
            self.recent_alerts.append(alert)
            
            # Keep only the most recent alerts
            if len(self.recent_alerts) > self.max_recent_alerts:
                self.recent_alerts = self.recent_alerts[-self.max_recent_alerts:]
                
            # Update alert count
            self.alert_count += 1
            
            # Print alert immediately if console is enabled
            if self.enable_console:
                alert_time = datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')
                print(f"{Fore.RED}[ALERT] [{alert_time}] {alert['type']}: {alert['details']}{Style.RESET_ALL}")
                
        except Exception as e:
            logger.error(f"Error adding alert: {e}")

    def get_alerts(self) -> List[dict]:
        """Get recent alerts"""
        return self.recent_alerts

    def clear_alerts(self):
        """Clear all alerts"""
        self.recent_alerts = []
        self.alert_count = 0