from pathlib import Path
from dataclasses import dataclass

@dataclass
class ServerConfig:
    HOST: str = "localhost"
    PORT: int = 8765
    DEBUG: bool = True
    SSL_ENABLED: bool = True
    MAX_CONNECTIONS: int = 100
    SCAN_INTERVAL: float = 2.0
    WORKERS: int = 4

@dataclass
class MonitoringConfig:
    PACKET_CAPTURE: bool = True
    PROCESS_TRACKING: bool = True
    TRAFFIC_ANALYSIS: bool = True
    AUTO_EXPORT: bool = True
    RETENTION_DAYS: int = 30

@dataclass
class LoggingConfig:
    LEVEL: str = "INFO"
    FILE: str = "logs/bigyellowjacket.log"
    MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5

@dataclass
class SecurityConfig:
    CERT_FILE: str = "certs/server.crt"
    KEY_FILE: str = "certs/server.key"
    BLOCKED_IPS_FILE: str = "data/blocked_ips.txt"
    KNOWN_MALICIOUS_PORTS: set = None

    def __post_init__(self):
        self.KNOWN_MALICIOUS_PORTS = {23, 445, 135, 3389, 21, 1433}

class Config:
    BASE_DIR = Path(__file__).parent.parent
    SERVER = ServerConfig()
    MONITORING = MonitoringConfig()
    LOGGING = LoggingConfig()
    SECURITY = SecurityConfig()

    @classmethod
    def create_directories(cls):
        directories = [
            "logs",
            "data",
            "data/alerts",
            "data/exports",
            "data/reports",
            "data/traffic",
            "data/threat_intel",
            "certs"
        ]
        for directory in directories:
            Path(cls.BASE_DIR / directory).mkdir(parents=True, exist_ok=True)
