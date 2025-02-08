from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Set, List, Optional, Any
from pathlib import Path

@dataclass
class ProcessInfo:
    """Detailed information about a process"""
    pid: int
    name: str = None
    path: str = None
    command_line: str = None
    username: str = None
    creation_time: datetime = None
    cpu_percent: float = 0
    memory_percent: float = 0
    status: str = None
    tcp_connections: int = 0
    udp_connections: int = 0
    read_bytes: int = 0
    write_bytes: int = 0
    
    def to_dict(self):
        return {k: str(v) if isinstance(v, datetime) else v 
                for k, v in asdict(self).items() if v is not None}

@dataclass
class TrafficSample:
    """Network traffic sample data"""
    timestamp: datetime
    source_port: int
    destination_port: int
    protocol: str
    payload_size: int
    is_encrypted: bool
    sample_data: str = None
    packet_type: str = None
    
    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class SecurityAssessment:
    """Security assessment results"""
    risk_level: str
    risk_factors: List[str] = field(default_factory=list)
    recommendation: str = None
    threat_indicators: List[str] = field(default_factory=list)
    trust_score: float = 0.0
    detection_rules_triggered: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)

@dataclass
class NetworkEndpoint:
    """Enhanced network endpoint information"""
    host: str
    port: int
    protocol: str
    process_info: ProcessInfo = None
    traffic_samples: List[TrafficSample] = field(default_factory=list)
    security_assessment: SecurityAssessment = None
    latency: float = 0
    is_safe: bool = False
    country: str = None
    city: str = None
    organization: str = None
    device_type: str = None
    open_ports: List[int] = field(default_factory=list)
    reverse_dns: str = None
    is_private: bool = False
    packet_loss: float = 0
    rtt_stats: dict = field(default_factory=dict)
    last_seen: datetime = None
    first_seen: datetime = None
    connection_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    avg_packet_size: float = 0
    connection_state: str = None
    encryption_type: str = None
    certificate_info: dict = field(default_factory=dict)
    dns_queries: List[str] = field(default_factory=list)
    http_requests: List[dict] = field(default_factory=list)
    behavioral_pattern: str = None
    
    def to_dict(self):
        data = asdict(self)
        for key in ['last_seen', 'first_seen']:
            if data[key]:
                data[key] = data[key].isoformat()
        if self.process_info:
            data['process_info'] = self.process_info.to_dict()
        if self.traffic_samples:
            data['traffic_samples'] = [sample.to_dict() for sample in self.traffic_samples]
        if self.security_assessment:
            data['security_assessment'] = self.security_assessment.to_dict()
        return {k: v for k, v in data.items() if v is not None}