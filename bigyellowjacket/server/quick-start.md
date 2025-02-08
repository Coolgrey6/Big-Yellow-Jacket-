## Step 6: Running the Program

1. Create a minimal threat intelligence database:
```bash
# Create initial threat intel file
echo '{"malicious_ips": [], "threat_patterns": []}' > data/threat_intel/database.json
touch data/threat_intel/malicious_ips.txt
```

2. Run the program:
```bash
# Windows (as Administrator)
python run.py

# Linux (with sudo for packet capture)
sudo python run.py
```

## Expected Output:
```
=================================================================================
    ____  _       __   __ _ _                 _            _        __ 
   / __ )(_)__ _ / /  / /(_) /__ ___ _    __/ /__ ____  (_)__ ___/ /_
  / __  / //  ' / _ \/ // /  ' \/ _ `/ |/|/ / / -_) __/ / / // _  / -_)
 /_/ /_/_//_/_/_.__/_//_/_/_/_/\_,_/|__,__/_/\__/_/ __/ /\_,_/_,_/\__/ 
                              Security Monitor v2.0
=================================================================================

█ System Status
├─ Uptime: 0:00:00
├─ Total Connections: 0
├─ Active Endpoints: 0
├─ Blocked IPs: 0
└─ Security Alerts: 0
```

## Troubleshooting Common First-Run Issues:

1. Permission Errors:
```bash
# Windows: Run as Administrator
# Linux: Run with sudo or add user to pcap group
sudo usermod -a -G pcap $USER
newgrp pcap
```

2. Missing Directories:
```bash
# Run directory creation script
python -c "from config.settings import Config; Config.create_directories()"
```

3. SSL Certificate Issues:
```bash
# Regenerate certificates
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 365 -nodes
```

4. Port Already in Use:
```bash
# Change port in config/settings.py
# Or kill process using the port
# Windows:
netstat -ano | findstr :8765
taskkill /PID <PID> /F

# Linux:
sudo lsof -i :8765
sudo kill <PID>
```

## Verifying Installation:

1. Check logs:
```bash
tail -f logs/bigyellowjacket.log
```

2. Monitor network connections:
- Open a web browser or make some network connections
- Watch the console output for detected connections

3. Test WebSocket connection:
```bash
# Using wscat (install with: npm install -g wscat)
wscat -c ws://localhost:8765
```

## Next Steps:

1. Configure custom settings in `config/settings.py`
2. Add known malicious IPs to `data/threat_intel/malicious_ips.txt`
3. Set up regular data exports in `MonitoringConfig`
4. Review and customize security rules

## Support:
For issues and questions:
1. Check the logs in `logs/bigyellowjacket.log`
2. Ensure all permissions are correctly set
3. Verify system requirements are met
