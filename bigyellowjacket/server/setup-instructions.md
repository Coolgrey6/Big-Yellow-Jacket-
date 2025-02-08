# Threat Intelligence Setup Instructions

## Directory Structure
```
bigyellowjacket/
├── data/
│   └── threat_intel/
│       ├── database.json        # Main threat database
│       ├── malicious_ips.txt    # Known malicious IP addresses
│       └── threat_patterns.json # Common attack patterns
├── src/
│   └── analyzers/
│       └── intelligence.py
├── setup_threat_intel.py       # Setup script
└── run.py                      # Main server script
```

## Setup Steps

1. Create the setup script:
```bash
# In your project root directory
touch setup_threat_intel.py
```

2. Copy the setup script content provided above into `setup_threat_intel.py`

3. Run the setup script before starting the server:
```bash
# Windows
python setup_threat_intel.py

# Linux/Mac
python3 setup_threat_intel.py
```

## Customizing Threat Intelligence

You can customize the threat intelligence by:

1. Adding known malicious IPs to `data/threat_intel/malicious_ips.txt`:
```text
192.0.2.1
198.51.100.0/24
203.0.113.0/24
```

2. Adding threat patterns to `data/threat_intel/threat_patterns.json`:
```json
{
  "name": "Custom Threat Pattern",
  "indicators": ["indicator1", "indicator2"],
  "severity": "HIGH"
}
```

3. Modifying risk scores in `data/threat_intel/database.json`

## Update Process

To update threat intelligence:

1. Manually:
   - Edit files in `data/threat_intel/`
   - Server will automatically load changes on next start

2. Via script:
   - Modify `setup_threat_intel.py`
   - Run script to update database

## Important Notes

- Run `setup_threat_intel.py` before first server start
- Backup existing threat intel before updates
- Keep threat intelligence updated regularly
- Consider adding your own known threats
- Monitor false positives and adjust accordingly

## Verification

To verify the setup:
```bash
# Check if files exist
ls -l data/threat_intel/

# View database content
cat data/threat_intel/database.json

# Check file permissions
ls -la data/threat_intel/
```
