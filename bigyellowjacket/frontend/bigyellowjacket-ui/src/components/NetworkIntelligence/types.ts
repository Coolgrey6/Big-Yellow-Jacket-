// src/components/NetworkIntelligence/types.ts
export interface NetworkData {
  host: string;
  port: number;
  protocol: string;
  processInfo?: {
    name: string;
    path: string;
    signature?: {
      verified: boolean;
      publisher: string;
      timestamp: string;
    };
  };
  metrics: {
    latency: number;
    bytesSent: number;
    bytesReceived: number;
  };
  security: {
    riskLevel: string;
    threats: string[];
    recommendation: string;
  };
  location?: {
    country: string;
    city: string;
    coordinates: [number, number];
    organization: string;
  };
}