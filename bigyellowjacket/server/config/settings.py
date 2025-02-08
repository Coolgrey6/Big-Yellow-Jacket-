from pathlib import Path
from dataclasses import dataclass

@dataclass
class ServerConfig:
    # Basic server settings
    HOST: str = "localhost"
    PORT: int = 8765  # Updated port to 8000
    SERVER_HOST="localhost"
    SERVER_PORT=8765
    DEBUG: bool = True
    SSL_ENABLED: bool = False
    MAX_CONNECTIONS: int = 100
    SCAN_INTERVAL: float = 2.0
    WORKERS: int = 4

    # WebSocket specific settings
    PING_INTERVAL: int = 20
    PING_TIMEOUT: int = 10
    MAX_MESSAGE_SIZE: int = 2**23  # 8MB
    BROADCAST_INTERVAL: float = 1.0  # seconds
    RECONNECT_DELAY: int = 5  # seconds

    # API endpoints
    API_VERSION: str = "v1"
    API_PREFIX: str = "/api"

@dataclass
class MonitoringConfig:
    PACKET_CAPTURE: bool = True
    PROCESS_TRACKING: bool = True
    TRAFFIC_ANALYSIS: bool = True
    AUTO_EXPORT: bool = True
    RETENTION_DAYS: int = 30
    
    # Connection settings
    CONNECTION_TIMEOUT: int = 300  # 5 minutes
    MAX_CACHED_ENTRIES: int = 1000
    HISTORY_SIZE: int = 100
    
    # Analysis settings
    SUSPICIOUS_THRESHOLD: float = 0.7
    THREAT_SCORE_THRESHOLD: float = 0.8
    ALERT_BATCH_SIZE: int = 100

@dataclass
class LoggingConfig:
    LEVEL: str = "INFO"
    FILE: str = "logs/bigyellowjacket.log"
    MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5
    
    # Additional logging settings
    CONSOLE_LOGGING: bool = True
    LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    ERROR_LOG: str = "logs/error.log"
    ACCESS_LOG: str = "logs/access.log"

@dataclass
class SecurityConfig:
    CERT_FILE: str = "certs/server.crt"
    KEY_FILE: str = "certs/server.key"
    BLOCKED_IPS_FILE: str = "data/blocked_ips.txt"
    KNOWN_MALICIOUS_PORTS: set = None
    
    # Additional security settings
    SSL_PROTOCOL: str = "TLS"
    MIN_TLS_VERSION: str = "TLSv1.2"
    CIPHER_STRING: str = "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256"
    DHPARAM_FILE: str = "certs/dhparam.pem"
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Authentication
    AUTH_REQUIRED: bool = False
    TOKEN_EXPIRY: int = 3600  # 1 hour
    
    # Threat Intelligence
    THREAT_INTEL_UPDATE_INTERVAL: int = 3600  # 1 hour
    THREAT_INTEL_SOURCES: list = None
    ALERT_THRESHOLD: int = 3

    def __post_init__(self):
        self.KNOWN_MALICIOUS_PORTS = {23, 445, 135, 3389, 21, 1433}
        self.THREAT_INTEL_SOURCES = [
            "data/threat_intel/database.json",
            "data/threat_intel/malicious_ips.txt",
            "data/threat_intel/threat_patterns.json"
        ]

@dataclass
class ExportConfig:
    # Export settings
    AUTO_EXPORT_INTERVAL: int = 3600  # 1 hour
    MAX_EXPORT_SIZE: int = 100 * 1024 * 1024  # 100MB
    COMPRESSION_ENABLED: bool = True
    COMPRESSION_TYPE: str = "gzip"
    
    # Export formats
    AVAILABLE_FORMATS: list = None
    DEFAULT_FORMAT: str = "json"
    
    # Export locations
    EXPORT_DIR: str = "data/exports"
    BACKUP_DIR: str = "data/exports/backup"
    
    def __post_init__(self):
        self.AVAILABLE_FORMATS = ["json", "csv", "yaml"]

class Config:
    BASE_DIR = Path(__file__).parent.parent
    SERVER = ServerConfig()
    MONITORING = MonitoringConfig()
    LOGGING = LoggingConfig()
    SECURITY = SecurityConfig()
    EXPORT = ExportConfig()

    @classmethod
    def create_directories(cls):
        directories = [
            "logs",
            "data",
            "data/alerts",
            "data/exports",
            "data/exports/backup",
            "data/reports",
            "data/traffic",
            "data/threat_intel",
            "certs",
            "data/stats"
        ]
        for directory in directories:
            Path(cls.BASE_DIR / directory).mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_path(cls, *paths) -> Path:
        """Get full path relative to BASE_DIR"""
        return cls.BASE_DIR.joinpath(*paths)

    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        required_files = [
            cls.SECURITY.CERT_FILE,
            cls.SECURITY.KEY_FILE,
        ]
        
        missing_files = [
            f for f in required_files 
            if not cls.get_path(f).exists()
        ]
        
        if missing_files and cls.SERVER.SSL_ENABLED:
            raise ValueError(f"Missing required files: {', '.join(missing_files)}")