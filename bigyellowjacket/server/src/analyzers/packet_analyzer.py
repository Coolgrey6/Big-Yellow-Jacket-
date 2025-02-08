import math
import re
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional
import struct
from src.utils.logger import logger
from src.models.datatypes import TrafficSample

class PacketAnalyzer:
    """Analyzes network packets for patterns and security threats"""
    
    def __init__(self):
        self.packet_history = deque(maxlen=1000)
        self.known_protocols = {
            20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "TELNET",
            25: "SMTP", 53: "DNS", 80: "HTTP", 443: "HTTPS",
            3389: "RDP", 5900: "VNC", 1433: "MSSQL", 3306: "MySQL"
        }
        self.suspicious_patterns = {
            rb'eval\(.*\)',  # Potential code execution
            rb'SELECT.*FROM',  # SQL queries
            rb'<script.*>',  # JavaScript injection
            rb'../\.\./',  # Directory traversal
            rb'cmd\.exe',  # Command execution
        }
        
    def analyze_packet(self, data: bytes, src_port: int, dst_port: int) -> Dict:
        """Analyze a single packet"""
        try:
            analysis = {
                'size': len(data),
                'is_encrypted': self.check_encryption(data),
                'protocol': self.detect_protocol(data, src_port, dst_port),
                'characteristics': self.analyze_characteristics(data),
                'timestamp': datetime.now(),
                'suspicious_score': self.calculate_suspicious_score(data)
            }
            
            self.packet_history.append(analysis)
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing packet: {e}")
            return {'error': str(e)}
    
    def check_encryption(self, data: bytes) -> bool:
        """Check if data appears to be encrypted using entropy analysis"""
        if len(data) < 20:
            return False
            
        try:
            # Calculate Shannon entropy
            entropy = 0
            byte_counts = [data.count(byte) for byte in range(256)]
            total_bytes = len(data)
            
            for count in byte_counts:
                if count:
                    probability = count / total_bytes
                    entropy -= probability * math.log2(probability)
                    
            # High entropy suggests encryption
            return entropy > 7.5
            
        except Exception as e:
            logger.error(f"Error checking encryption: {e}")
            return False
    
    def detect_protocol(self, data: bytes, src_port: int, dst_port: int) -> str:
        """Detect the protocol being used"""
        try:
            # Check well-known ports first
            for port in [src_port, dst_port]:
                if port in self.known_protocols:
                    return self.known_protocols[port]
            
            # Protocol signatures
            signatures = {
                'HTTP': [b'HTTP/', b'GET ', b'POST ', b'HEAD '],
                'SSH': [b'SSH-'],
                'TLS': [b'\x16\x03', b'\x17\x03'],
                'DNS': [b'\x00\x00\x01\x00\x00\x01\x00\x00'],
                'SMTP': [b'EHLO', b'HELO', b'MAIL FROM'],
                'FTP': [b'220 ', b'USER ', b'PASS '],
                'TELNET': [b'\xff\xfb', b'\xff\xfd'],
            }
            
            for protocol, sigs in signatures.items():
                if any(sig in data[:20] for sig in sigs):
                    return protocol
                    
            return 'UNKNOWN'
            
        except Exception as e:
            logger.error(f"Error detecting protocol: {e}")
            return 'UNKNOWN'
    
    def analyze_characteristics(self, data: bytes) -> Dict:
        """Analyze packet characteristics"""
        try:
            return {
                'has_binary': any(b < 32 and b not in {9, 10, 13} for b in data),
                'has_printable': any(32 <= b <= 126 for b in data),
                'has_high_byte': any(b > 126 for b in data),
                'pattern': self.detect_pattern(data),
                'common_strings': self.find_common_strings(data),
                'suspicious_patterns': self.detect_suspicious_patterns(data)
            }
        except Exception as e:
            logger.error(f"Error analyzing characteristics: {e}")
            return {}
    
    def detect_pattern(self, data: bytes) -> str:
        """Detect common data patterns"""
        patterns = {
            'EXECUTABLE': [(0, b'MZ'), (0, b'ELF')],
            'ARCHIVE': [(0, b'PK'), (0, b'Rar!')],
            'IMAGE': [(0, b'\x89PNG'), (0, b'JFIF'), (0, b'GIF8')],
            'PDF': [(0, b'%PDF')],
            'JAVASCRIPT': [(None, b'function'), (None, b'eval(')],
            'HTML': [(None, b'<!DOCTYPE'), (None, b'<html')],
            'XML': [(None, b'<?xml')],
        }
        
        for pattern_type, signatures in patterns.items():
            for offset, signature in signatures:
                if offset is None and signature in data:
                    return pattern_type
                elif offset is not None and data[offset:offset+len(signature)] == signature:
                    return pattern_type
                    
        return 'UNKNOWN'
    
    def find_common_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Find common strings in packet data"""
        strings = []
        current = []
        
        try:
            for byte in data:
                if 32 <= byte <= 126:  # printable ASCII
                    current.append(chr(byte))
                elif current:
                    if len(current) >= min_length:
                        strings.append(''.join(current))
                    current = []
            
            # Add any remaining string
            if current and len(current) >= min_length:
                strings.append(''.join(current))
                
            return strings[:10]  # Return top 10 strings
            
        except Exception as e:
            logger.error(f"Error finding common strings: {e}")
            return []
    
    def detect_suspicious_patterns(self, data: bytes) -> List[str]:
        """Detect suspicious patterns in the data"""
        detected = []
        try:
            for pattern in self.suspicious_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    detected.append(pattern.decode('utf-8', errors='ignore'))
            return detected
        except Exception as e:
            logger.error(f"Error detecting suspicious patterns: {e}")
            return []
    
    def calculate_suspicious_score(self, data: bytes) -> float:
        """Calculate a suspicion score for the packet"""
        score = 0.0
        try:
            # Check for suspicious patterns
            score += len(self.detect_suspicious_patterns(data)) * 0.2
            
            # Check for unusual characteristics
            chars = self.analyze_characteristics(data)
            if chars.get('has_binary') and chars.get('has_high_byte'):
                score += 0.3
                
            # Check entropy
            if self.check_encryption(data):
                score += 0.1
                
            # Normalize score between 0 and 1
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating suspicious score: {e}")
            return 0.0

    def get_packet_statistics(self) -> Dict:
        """Get statistical analysis of recent packets"""
        try:
            if not self.packet_history:
                return {}
                
            sizes = [p['size'] for p in self.packet_history]
            protocols = [p['protocol'] for p in self.packet_history]
            
            return {
                'avg_size': sum(sizes) / len(sizes),
                'max_size': max(sizes),
                'min_size': min(sizes),
                'protocol_distribution': {
                    proto: protocols.count(proto) / len(protocols)
                    for proto in set(protocols)
                },
                'encrypted_ratio': sum(
                    1 for p in self.packet_history if p['is_encrypted']
                ) / len(self.packet_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting packet statistics: {e}")
            return {}