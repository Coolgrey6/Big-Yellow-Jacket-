# Big Yellow Jacket Network Analyzer - Installation Guide

## Directory Structure
```
bigyellowjacket/
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   ├── alerts/
│   ├── exports/
│   ├── reports/
│   └── traffic/
├── logs/
├── certs/
├── src/
│   ├── __init__.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── packet_analyzer.py
│   │   └── intelligence.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── console.py
│   │   ├── monitor.py
│   │   └── websocket.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── datatypes.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── security.py
├── tests/
├── requirements.txt
├── setup.py
└── run.py

## Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bigyellowjacket.git
cd bigyellowjacket
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Generate SSL certificates (optional but recommended):
```bash
mkdir certs
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 365 -nodes
```

5. Configure settings:
- Edit `config/settings.py` to customize your configuration
- Ensure all required directories exist

6. Run the application:
```bash
python run.py
```

## System Requirements

- Python 3.8 or higher
- For packet capture:
  - Windows: Npcap or WinPcap installed
  - Linux: tcpdump installed
- Administrative privileges for packet capture

## Additional Setup

### Windows-specific
1. Install Npcap from https://npcap.org
2. Run the application as Administrator

### Linux-specific
1. Install tcpdump:
```bash
sudo apt-get install tcpdump
```

2. Add user to pcap group:
```bash
sudo usermod -a -G pcap $USER
```

## Usage

1. Start the server:
```bash
python run.py
```

2. Access the web interface:
- Open a browser and navigate to `https://localhost:8765` (or your configured host/port)
- Accept the self-signed certificate if using SSL

3. Monitor network activity:
- View real-time connections
- Analyze traffic patterns
- Manage blocked IPs
- Export data and reports

## Common Issues

1. Permission denied for packet capture:
   - Ensure running with administrative privileges
   - Check pcap group membership on Linux

2. SSL certificate errors:
   - Generate new certificates following step 4
   - Use properly signed certificates in production

3. Port already in use:
   - Change the port in config/settings.py
   - Check for other applications using the port

## Security Considerations

1. Production deployment:
   - Use proper SSL certificates
   - Configure firewall rules
   - Implement authentication
   - Regular security updates

2. Data handling:
   - Implement data retention policies
   - Secure sensitive data
   - Regular backup procedures

## Support

For issues and feature requests, please create an issue in the GitHub repository.
