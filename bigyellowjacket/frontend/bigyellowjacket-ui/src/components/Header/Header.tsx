import React from 'react';
import { Shield } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="bg-secondary text-white">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold font-mono">Big Yellow Jacket Security</h1>
              <p className="text-sm font-mono text-gray-400">by Donnie Bugden V 1.0</p>
            </div>
          </div>
          <a 
            href="https://bigyellowjacket.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-primary hover:text-primary-light transition-colors"
          >
            bigyellowjacket.com
          </a>
        </div>
      </div>
    </header>
  );
};