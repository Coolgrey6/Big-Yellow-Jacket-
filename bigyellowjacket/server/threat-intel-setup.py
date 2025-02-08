import json
import os
from pathlib import Path

def setup_threat_intel():
    """Setup initial threat intelligence database"""
    # Create base directories
    base_dir = Path("data/threat_intel")
    base_dir.mkdir(parents=True, exist_ok=True)

    # Initial threat intelligence database
    database = {
        "malicious_ips": [],
        "threat_patterns": [
            {
                "name": "SQL Injection",
                "pattern": r"(?i)(union|select|insert|delete|update|drop|--)",
                "risk_level": "HIGH"
            },
            {
                "name": "Command Injection",
                "pattern": r"(?i)(cmd\.exe|/bin/sh|/bin/bash|\|\||&&)",
                "risk_level": "CRITICAL"
            },
            {
                "name": "Port Scan",
                "pattern": r"multiple_ports_accessed",
                "risk_level": "MEDIUM"
            }
        ],
        "known_threats": {
            "ransomware": {
                "ports": [445, 139, 3389],
                "risk_level": "CRITICAL"
            },
            "botnet": {
                "ports": [6667, 1080, 25],
                "risk_level": "HIGH"
            }
        },
        "risk_scores": {
            "known_malicious": 1.0,
            "suspicious_port": 0.7,
            "unusual_traffic": 0.5,
            "unknown_process": 0.3
        }
    }

    # Example malicious IPs (you should update these with real threat intel)
    malicious_ips = [
        "185.159.83.0/24",  # Example range
        "91.134.183.0/24",  # Example range
        "198.51.100.0/24",  # Example range
    ]

    # Example threat patterns
    threat_patterns = [
        {
            "name": "Data Exfiltration",
            "indicators": [
                "large_outbound_traffic",
                "encrypted_tunnel",
                "unusual_ports"
            ],
            "severity": "HIGH"
        },
        {
            "name": "Lateral Movement",
            "indicators": [
                "multiple_internal_connections",
                "credential_access",
                "admin_share_access"
            ],
            "severity": "HIGH"
        }
    ]

    # Write files
    files_to_create = {
        "database.json": database,
        "malicious_ips.txt": "\n".join(malicious_ips),
        "threat_patterns.json": threat_patterns
    }

    for filename, content in files_to_create.items():
        file_path = base_dir / filename
        if isinstance(content, (dict, list)):
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
            print(f"Created {file_path}")
        else:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created {file_path}")

if __name__ == "__main__":
    setup_threat_intel()
    print("Threat intelligence database initialized successfully!")
