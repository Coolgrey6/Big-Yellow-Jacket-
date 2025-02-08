// src/components/Dashboard/AlertCard.tsx

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface Alert {
  timestamp: string;
  type: string;
  endpoint: {
    host: string;
    port: number;
  };
  details: {
    count?: number;
    [key: string]: any;
  };
}

interface AlertCardProps {
  alerts: Alert[];
}

const AlertCard: React.FC<AlertCardProps> = ({ alerts }) => {
  const getAlertMessage = (alert: Alert) => {
    switch (alert.type) {
      case 'rapid_reconnection':
        return `Rapid reconnection from ${alert.endpoint.host}:${alert.endpoint.port} (${alert.details.count} attempts)`;
      case 'suspicious_activity':
        return `Suspicious activity detected from ${alert.endpoint.host}:${alert.endpoint.port}`;
      case 'connection_blocked':
        return `Connection blocked: ${alert.endpoint.host}:${alert.endpoint.port}`;
      default:
        return `${alert.type}: ${alert.endpoint.host}:${alert.endpoint.port}`;
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
      <div className="flex items-center space-x-2 mb-4">
        <AlertCircle className="w-5 h-5 text-red-500" />
        <h3 className="font-medium">Recent Alerts</h3>
      </div>
      <div className="space-y-3">
        {alerts && alerts.length > 0 ? (
          alerts.slice(0, 5).map((alert, index) => (
            <div key={index} className="flex items-start space-x-2">
              <span className="text-red-500 mt-1">●</span>
              <div className="flex-1">
                <div className="text-sm font-medium">
                  {getAlertMessage(alert)}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(alert.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-gray-500 text-sm">No recent alerts</div>
        )}
      </div>
    </div>
  );
};

export default AlertCard;