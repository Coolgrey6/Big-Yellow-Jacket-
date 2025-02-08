import asyncio
import sys
import signal
from pathlib import Path
from src.utils.logger import logger
from src.core.monitor import NetworkMonitor
from src.core.console import ConsoleMonitor
from src.core.websocket import WebSocketServer
from config.settings import Config

async def main():
    """Main application entry point"""
    try:
        # Initialize components
        console_monitor = ConsoleMonitor(enable_console=True)
        network_monitor = NetworkMonitor(console_monitor)
        websocket_server = WebSocketServer(network_monitor, console_monitor)
        
        # Start console updates
        console_task = asyncio.create_task(console_monitor.start_updates())
        
        # Start network monitoring
        monitor_task = asyncio.create_task(network_monitor.start_monitoring())
        
        # Start WebSocket server
        websocket_task = asyncio.create_task(websocket_server.start())
        
        # Handle shutdown gracefully
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received...")
            console_monitor.stop_updates()
            for task in [console_task, monitor_task, websocket_task]:
                task.cancel()
            
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for tasks
        try:
            await asyncio.gather(console_task, monitor_task, websocket_task)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled, shutting down...")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    try:
        # Ensure required directories exist
        for dir_name in ['logs', 'data', 'certs']:
            Path(dir_name).mkdir(exist_ok=True)
        
        # Print startup banner
        print("""
[Big Yellow Jacket Security
by Donnie Bugden V 1.0
https://bigyellowjacket.com
]
        """)
        
        # Run the application
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        sys.exit(1)