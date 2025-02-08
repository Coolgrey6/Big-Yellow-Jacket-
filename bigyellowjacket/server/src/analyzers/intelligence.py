import asyncio
import socket
import subprocess
import platform
from datetime import datetime
from typing import Dict, Optional, List, Set
import ipaddress
from pathlib import Path
import json
import re
import math
import psutil
from src.utils.logger import logger
from src.models.datatypes import NetworkEndpoint, ProcessInfo, TrafficSample, SecurityAssessment

class NetworkIntelligenceGatherer:
    """Gathers intelligence about network endpoints and performs security analysis"""
    
    def __init__(self, console_monitor):
        # System and monitoring setup
        self.system = platform.system().lower()
        self.console = console_monitor
        self.connection_history: Dict[str, Dict] = {}
        
        # Caching mechanisms
        self.dns_cache: Dict[str, Dict] = {}
        self.location_cache: Dict[str, Dict] = {}
        self.process_cache: Dict[int, ProcessInfo] = {}
        self.dns_cache_timeout = 3600  # 1 hour
        
        # Load threat intelligence database
        self.threat_intel_db = self.load_threat_intel()
        self.known_safe_processes: Set[str] = {
            'chrome.exe', 'firefox.exe', 'safari',
            'outlook.exe', 'thunderbird', 'code',
            'python', 'node', 'nginx', 'apache2'
        }
        
        # Analysis configuration
        self.packet_capture_timeout = 5  # seconds
        self.max_port_scan_timeout = 1  # second
        self.max_cached_entries = 1000
        self.suspicious_ports = {23, 445, 135, 3389}
        
    def load_threat_intel(self) -> Dict:
        """Load threat intelligence data from local database"""
        try:
            intel_paths = {
                'main': Path("data/threat_intel/database.json"),
                'ip_lists': Path("data/threat_intel/malicious_ips.txt"),
                'patterns': Path("data/threat_intel/threat_patterns.json")
            }
            
            threat_data = {
                'malicious_ips': set(),
                'threat_patterns': [],
                'risk_scores': {},
                'known_threats': {}
            }
            
            # Load main database
            if intel_paths['main'].exists():
                with open(intel_paths['main']) as f:
                    main_data = json.load(f)
                    if 'malicious_ips' in main_data:
                        threat_data['malicious_ips'] = set(main_data['malicious_ips'])
                    for key in ['threat_patterns', 'risk_scores', 'known_threats']:
                        if key in main_data:
                            threat_data[key] = main_data[key]
            
            # Load IP lists
            if intel_paths['ip_lists'].exists():
                with open(intel_paths['ip_lists']) as f:
                    malicious_ips = {
                        line.strip() for line in f 
                        if line.strip() and not line.startswith('#')
                    }
                    threat_data['malicious_ips'].update(malicious_ips)
            
            # Load threat patterns
            if intel_paths['patterns'].exists():
                with open(intel_paths['patterns']) as f:
                    patterns = json.load(f)
                    threat_data['threat_patterns'] = patterns
            
            logger.info(f"Loaded threat intelligence data: "
                       f"{len(threat_data['malicious_ips'])} IPs, "
                       f"{len(threat_data['threat_patterns'])} patterns")
            
            return threat_data
            
        except Exception as e:
            logger.error(f"Error loading threat intelligence: {e}")
            return {
                'malicious_ips': set(),
                'threat_patterns': [],
                'risk_scores': {},
                'known_threats': {}
            }
    
    def cleanup_caches(self):
        """Clean up expired cache entries"""
        current_time = datetime.now().timestamp()
        
        # Clean DNS cache
        expired_dns = [
            ip for ip, data in self.dns_cache.items()
            if current_time - data.get('timestamp', 0) > self.dns_cache_timeout
        ]
        for ip in expired_dns:
            del self.dns_cache[ip]
            
        # Clean location cache if too large
        if len(self.location_cache) > self.max_cached_entries:
            self.location_cache.clear()
            
        # Clean process cache
        expired_processes = [
            pid for pid in self.process_cache
            if not psutil.pid_exists(pid)
        ]
        for pid in expired_processes:
            del self.process_cache[pid]

    def is_private_ip(self, ip: str) -> bool:
        """Check if IP address is private"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return any([
                ip_obj.is_private,
                ip_obj.is_loopback,
                ip_obj.is_link_local,
                ip_obj.is_multicast,
                str(ip_obj).startswith('169.254.'),  # Link local
                str(ip_obj).startswith('127.'),      # Loopback
                str(ip_obj).startswith('0.'),        # Invalid
                str(ip_obj).startswith('224.'),      # Multicast
            ])
        except ValueError:
            logger.error(f"Invalid IP address: {ip}")
            return False

    async def gather_intelligence(self, endpoint: NetworkEndpoint) -> NetworkEndpoint:
        """Gather comprehensive intelligence about an endpoint"""
        try:
            # Run intelligence gathering tasks concurrently
            dns_task = asyncio.create_task(self.get_dns_info(endpoint.host))
            ports_task = asyncio.create_task(self.scan_ports(endpoint.host))
            latency_task = asyncio.create_task(self.measure_latency(endpoint.host))
            traffic_task = asyncio.create_task(self.capture_traffic(endpoint))
            process_task = asyncio.create_task(self.get_process_info(endpoint))
            location_task = asyncio.create_task(self.get_location_info(endpoint.host))
            
            # Await all tasks
            results = await asyncio.gather(
                dns_task, ports_task, latency_task, 
                traffic_task, process_task, location_task,
                return_exceptions=True
            )
            
            # Unpack results
            dns_info, open_ports, latency_info, traffic_info, process_info, location_info = results
            
            # Update endpoint with gathered information
            await self.update_endpoint_info(
                endpoint, dns_info, open_ports, latency_info,
                traffic_info, process_info, location_info
            )
            
            # Perform security assessment
            endpoint.security_assessment = await self.assess_security(endpoint)
            endpoint.is_safe = endpoint.security_assessment.risk_level in ['LOW', 'MEDIUM']
            
            # Update history and cleanup
            self.update_history(endpoint)
            self.cleanup_caches()
            
            return endpoint
            
        except Exception as e:
            logger.error(f"Error gathering intelligence for {endpoint.host}: {e}")
            return endpoint

    async def update_endpoint_info(
        self, endpoint: NetworkEndpoint,
        dns_info: Dict, open_ports: List[int],
        latency_info: Dict, traffic_info: Dict,
        process_info: ProcessInfo, location_info: Dict
    ):
        """Update endpoint with gathered information"""
        try:
            # Update DNS information
            if isinstance(dns_info, dict):
                endpoint.reverse_dns = dns_info.get('hostname')
                endpoint.is_private = self.is_private_ip(endpoint.host)
            
            # Update port information
            if isinstance(open_ports, list):
                endpoint.open_ports = open_ports
            
            # Update latency information
            if isinstance(latency_info, dict):
                endpoint.latency = latency_info.get('avg_rtt', 0)
                endpoint.packet_loss = latency_info.get('packet_loss', 0)
                endpoint.rtt_stats = latency_info
            
            # Update process information
            if isinstance(process_info, ProcessInfo):
                endpoint.process_info = process_info
            
            # Update location information
            if isinstance(location_info, dict):
                endpoint.country = location_info.get('country')
                endpoint.city = location_info.get('city')
                endpoint.organization = location_info.get('org')
            
            # Update traffic information
            if isinstance(traffic_info, dict):
                endpoint.traffic_samples = traffic_info.get('samples', [])
                endpoint.encryption_type = traffic_info.get('encryption_type')
                endpoint.bytes_sent = traffic_info.get('bytes_sent', 0)
                endpoint.bytes_received = traffic_info.get('bytes_received', 0)
                endpoint.avg_packet_size = self.calculate_avg_packet_size(
                    traffic_info.get('samples', [])
                )
                
        except Exception as e:
            logger.error(f"Error updating endpoint info: {e}")

    async def get_dns_info(self, host: str) -> Dict:
        """Get DNS information about a host"""
        if host in self.dns_cache:
            cache_entry = self.dns_cache[host]
            if datetime.now().timestamp() - cache_entry['timestamp'] < self.dns_cache_timeout:
                return cache_entry['data']
        
        try:
            # Use socket for forward and reverse DNS
            loop = asyncio.get_event_loop()
            
            # Forward lookup
            try:
                addresses = await loop.run_in_executor(None, socket.gethostbyname_ex, host)
                hostname = await loop.run_in_executor(None, socket.gethostbyaddr, host)
            except (socket.gaierror, socket.herror):
                addresses = (None, None, [host])
                hostname = (None, None, None)

            info = {
                'hostname': hostname[0] if hostname[0] else None,
                'addresses': addresses[2] if addresses[2] else [host],
                'ttl': 0
            }
            
            # Cache the result
            self.dns_cache[host] = {
                'timestamp': datetime.now().timestamp(),
                'data': info
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting DNS info for {host}: {e}")
            return {'hostname': None, 'addresses': [host], 'ttl': 0}

    async def get_process_info(self, endpoint: NetworkEndpoint) -> Optional[ProcessInfo]:
        """Get information about the process using this connection"""
        try:
            # Check process cache first
            if hasattr(endpoint, 'pid') and endpoint.pid in self.process_cache:
                return self.process_cache[endpoint.pid]

            # Get all network connections
            loop = asyncio.get_event_loop()
            connections = await loop.run_in_executor(None, psutil.net_connections)
            
            for conn in connections:
                try:
                    if (conn.raddr and 
                        conn.raddr[0] == endpoint.host and 
                        conn.raddr[1] == endpoint.port):
                        
                        process = psutil.Process(conn.pid)
                        
                        # Create process info
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
                        
                        # Cache the process info
                        self.process_cache[conn.pid] = process_info
                        return process_info
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logger.debug(f"Error getting process info: {e}")
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting process info for {endpoint.host}: {e}")
            return None

    async def get_location_info(self, host: str) -> Dict:
        """Get geographical location information for an IP"""
        if host in self.location_cache:
            return self.location_cache[host]
            
        try:
            # This is a placeholder - implement actual IP geolocation
            info = {
                'country': 'Unknown',
                'city': 'Unknown',
                'org': 'Unknown'
            }
            
            self.location_cache[host] = info
            return info
            
        except Exception as e:
            logger.error(f"Error getting location info: {e}")
            return {
                'country': 'Unknown',
                'city': 'Unknown',
                'org': 'Unknown'
            }

    async def measure_latency(self, host: str) -> Dict:
        """Measure network latency to the host with improved timeout handling"""
        try:
            # Reduced ping count and timeout for faster measurements
            if self.system == "windows":
                cmd = f"ping -n 2 -w 1000 {host}"  # 2 pings, 1 second timeout
                parse_loss = r"(\d+)% loss"
                parse_time = r"time[=<](\d+)ms"
            else:
                cmd = f"ping -c 2 -W 1 {host}"  # 2 pings, 1 second timeout
                parse_loss = r"(\d+)% packet loss"
                parse_time = r"time=(\d+\.\d+) ms"
            
            # Execute ping command with timeout
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=2.0)
                output = stdout.decode()
                
                # Parse results
                loss_match = re.search(parse_loss, output)
                time_matches = re.findall(parse_time, output)
                
                packet_loss = float(loss_match.group(1)) if loss_match else 100
                times = [float(t) for t in time_matches] if time_matches else []
                
                if not times:
                    # If no successful pings, return high latency values
                    return {
                        "packet_loss": 100,
                        "min_rtt": 1000,
                        "max_rtt": 1000,
                        "avg_rtt": 1000,
                        "samples": 0,
                        "status": "timeout"
                    }
                
                return {
                    "packet_loss": packet_loss,
                    "min_rtt": min(times) if times else 1000,
                    "max_rtt": max(times) if times else 1000,
                    "avg_rtt": sum(times) / len(times) if times else 1000,
                    "samples": len(times),
                    "status": "success"
                }
            except asyncio.TimeoutError:
                # Handle timeout more gracefully
                logger.debug(f"Latency measurement timeout for {host}")
                return {
                    "packet_loss": 100,
                    "min_rtt": 1000,
                    "max_rtt": 1000,
                    "avg_rtt": 1000,
                    "samples": 0,
                    "status": "timeout"
                }
                
        except Exception as e:
            logger.debug(f"Error measuring latency to {host}: {str(e)}")
            return {
                "packet_loss": 100,
                "min_rtt": 1000,
                "max_rtt": 1000,
                "avg_rtt": 1000,
                "samples": 0,
                "status": "error",
                "error": str(e)
            }

    async def scan_ports(self, host: str) -> List[int]:
        """Scan common ports on the host"""
        open_ports = []
        common_ports = [20, 21, 22, 23, 25, 53, 80, 443, 3389, 5900]
        
        try:
            async def check_port(port):
                try:
                    future = asyncio.open_connection(host, port)
                    reader, writer = await asyncio.wait_for(
                        future, timeout=self.max_port_scan_timeout
                    )
                    writer.close()
                    await writer.wait_closed()
                    return port
                except:
                    return None
            
            # Scan ports concurrently
            tasks = [check_port(port) for port in common_ports]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            open_ports = [port for port in results if isinstance(port, int) and port is not None]
            
            return open_ports
            
        except Exception as e:
            logger.error(f"Error scanning ports for {host}: {e}")
            return []

    async def capture_traffic(self, endpoint: NetworkEndpoint) -> Dict:
        """Capture and analyze traffic for the endpoint"""
        try:
            # For Windows, use netstat instead of packet capture
            if self.system == "windows":
                return await self.get_connection_info_windows(endpoint)
            else:
                return await self.get_connection_info_linux(endpoint)
        except Exception as e:
            logger.error(f"Error capturing traffic: {e}")
            return {
                'samples': [],
                'encryption_type': 'UNKNOWN',
                'bytes_sent': 0,
                'bytes_received': 0
            }

    async def get_connection_info_windows(self, endpoint: NetworkEndpoint) -> Dict:
        """Get connection information using netstat on Windows"""
        try:
            cmd = f"netstat -n -p TCP | findstr {endpoint.host}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
                connections = stdout.decode().splitlines()
                samples = []
                bytes_sent = 0
                bytes_received = 0
                
                for conn in connections:
                    parts = conn.split()
                    if len(parts) >= 4:
                        try:
                            source_port = int(parts[1].split(':')[-1])
                            dest_port = int(parts[2].split(':')[-1])
                            samples.append(TrafficSample(
                                timestamp=datetime.now(),
                                source_port=source_port,
                                destination_port=dest_port,
                                protocol='TCP',
                                payload_size=0,
                                is_encrypted=endpoint.port == 443,
                                packet_type='TCP'
                            ))
                        except (ValueError, IndexError) as e:
                            continue
                
                return {
                    'samples': samples,
                    'encryption_type': 'SSL/TLS' if endpoint.port == 443 else 'NONE',
                    'bytes_sent': bytes_sent,
                    'bytes_received': bytes_received
                }
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout getting Windows connection info for {endpoint.host}")
                return {
                    'samples': [],
                    'encryption_type': 'UNKNOWN',
                    'bytes_sent': 0,
                    'bytes_received': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting Windows connection info: {str(e)}")
            return {
                'samples': [],
                'encryption_type': 'UNKNOWN',
                'bytes_sent': 0,
                'bytes_received': 0
            }

    async def get_connection_info_linux(self, endpoint: NetworkEndpoint) -> Dict:
        """Get connection information using ss on Linux"""
        try:
            cmd = f"ss -tn dst {endpoint.host}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
                connections = stdout.decode().splitlines()[1:]  # Skip header
                samples = []
                bytes_sent = 0
                bytes_received = 0
                
                for conn in connections:
                    parts = conn.split()
                    if len(parts) >= 4:
                        try:
                            source_port = int(parts[2].split(':')[-1])
                            dest_port = int(parts[3].split(':')[-1])
                            samples.append(TrafficSample(
                                timestamp=datetime.now(),
                                source_port=source_port,
                                destination_port=dest_port,
                                protocol='TCP',
                                payload_size=0,
                                is_encrypted=endpoint.port == 443,
                                packet_type='TCP'
                            ))
                        except (ValueError, IndexError):
                            continue
                
                return {
                    'samples': samples,
                    'encryption_type': 'SSL/TLS' if endpoint.port == 443 else 'NONE',
                    'bytes_sent': bytes_sent,
                    'bytes_received': bytes_received
                }
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout getting Linux connection info for {endpoint.host}")
                return {
                    'samples': [],
                    'encryption_type': 'UNKNOWN',
                    'bytes_sent': 0,
                    'bytes_received': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting Linux connection info: {str(e)}")
            return {
                'samples': [],
                'encryption_type': 'UNKNOWN',
                'bytes_sent': 0,
                'bytes_received': 0
            }

    def calculate_avg_packet_size(self, samples: List[TrafficSample]) -> float:
        """Calculate average packet size from samples"""
        if not samples:
            return 0.0
        return sum(sample.payload_size for sample in samples) / len(samples)

    async def assess_security(self, endpoint: NetworkEndpoint) -> SecurityAssessment:
        """Assess security risks for an endpoint"""
        risk_factors = []
        threat_indicators = []
        
        try:
            # Check known malicious indicators
            if str(endpoint.host) in self.threat_intel_db.get('malicious_ips', set()):
                threat_indicators.append(f"IP {endpoint.host} is known malicious")
                
            if endpoint.port in self.suspicious_ports:
                threat_indicators.append(f"Port {endpoint.port} is suspicious")
                
            # Check traffic patterns
            if endpoint.traffic_samples:
                encrypted_ratio = sum(1 for s in endpoint.traffic_samples if s.is_encrypted)
                if encrypted_ratio and len(endpoint.traffic_samples) > 0:
                    if encrypted_ratio / len(endpoint.traffic_samples) > 0.9:
                        risk_factors.append("High ratio of encrypted traffic")
                    
            # Check process legitimacy
            if endpoint.process_info and endpoint.process_info.name:
                if endpoint.process_info.name not in self.known_safe_processes:
                    risk_factors.append(f"Suspicious process: {endpoint.process_info.name}")
                    
            # Calculate trust score
            trust_score = self.calculate_trust_score(endpoint, threat_indicators)
            
            # Determine risk level
            risk_level = self.determine_risk_level(trust_score, threat_indicators)
            
            # Get recommendation
            recommendation = self.get_recommendation(risk_level)
            
            return SecurityAssessment(
                risk_level=risk_level,
                risk_factors=risk_factors,
                threat_indicators=threat_indicators,
                trust_score=trust_score,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error in security assessment: {e}")
            return SecurityAssessment(
                risk_level="UNKNOWN",
                risk_factors=[],
                threat_indicators=[],
                trust_score=0.0,
                recommendation="Error performing security assessment"
            )

    def calculate_trust_score(self, endpoint: NetworkEndpoint, threat_indicators: List[str]) -> float:
        """Calculate trust score for endpoint"""
        try:
            score = 1.0
            
            # Reduce score based on threats
            score -= len(threat_indicators) * 0.2
            
            # Consider connection history
            if endpoint.connection_count > 100:
                score += 0.1
                
            # Consider performance metrics
            if hasattr(endpoint, 'packet_loss') and endpoint.packet_loss > 50:
                score -= 0.1
                
            if hasattr(endpoint, 'latency') and endpoint.latency > 500:
                score -= 0.1
                
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating trust score: {e}")
            return 0.0

    def determine_risk_level(self, trust_score: float, threat_indicators: List[str]) -> str:
        """Determine risk level based on trust score"""
        try:
            if len(threat_indicators) > 2:
                return "CRITICAL"
            elif trust_score < 0.3:
                return "HIGH"
            elif trust_score < 0.6:
                return "MEDIUM"
            else:
                return "LOW"
        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return "UNKNOWN"

    def get_recommendation(self, risk_level: str) -> str:
        """Get security recommendation based on risk level"""
        recommendations = {
            "CRITICAL": "Immediate action required: Block this connection and investigate",
            "HIGH": "Recommended action: Monitor closely and consider blocking",
            "MEDIUM": "Caution advised: Monitor for suspicious behavior",
            "LOW": "Normal monitoring recommended",
            "UNKNOWN": "Unable to determine risk level - manual investigation recommended"
        }
        return recommendations.get(risk_level, "Unknown risk level - manual investigation recommended")

    def update_history(self, endpoint: NetworkEndpoint):
        """Update connection history"""
        try:
            key = f"{endpoint.host}:{endpoint.port}"
            
            if key not in self.connection_history:
                self.connection_history[key] = {
                    'first_seen': datetime.now(),
                    'connection_count': 1,
                    'bytes_total': endpoint.bytes_sent + endpoint.bytes_received,
                    'risk_levels': []
                }
            
            history = self.connection_history[key]
            history['connection_count'] += 1
            history['bytes_total'] += endpoint.bytes_sent + endpoint.bytes_received
            
            if endpoint.security_assessment and endpoint.security_assessment.risk_level:
                history['risk_levels'].append(endpoint.security_assessment.risk_level)
                # Keep only last 100 risk levels
                if len(history['risk_levels']) > 100:
                    history['risk_levels'] = history['risk_levels'][-100:]
                    
        except Exception as e:
            logger.error(f"Error updating history: {e}")

    def export_endpoint_data(self, endpoint: NetworkEndpoint, format: str = 'json') -> str:
        """Export endpoint data in specified format"""
        try:
            data = {
                'host': endpoint.host,
                'port': endpoint.port,
                'protocol': endpoint.protocol,
                'first_seen': endpoint.first_seen.isoformat() if endpoint.first_seen else None,
                'last_seen': endpoint.last_seen.isoformat() if endpoint.last_seen else None,
                'connection_count': endpoint.connection_count,
                'bytes_sent': endpoint.bytes_sent,
                'bytes_received': endpoint.bytes_received,
                'is_safe': endpoint.is_safe,
                'risk_assessment': endpoint.security_assessment.to_dict() if endpoint.security_assessment else None,
                'process_info': endpoint.process_info.to_dict() if endpoint.process_info else None,
                'traffic_samples': [sample.to_dict() for sample in endpoint.traffic_samples] if endpoint.traffic_samples else []
            }
            
            if format.lower() == 'json':
                return json.dumps(data, indent=2)
            elif format.lower() == 'csv':
                # Implement CSV export if needed
                pass
            else:
                return str(data)
                
        except Exception as e:
            logger.error(f"Error exporting endpoint data: {e}")
            return str({'error': f"Failed to export data: {str(e)}"})