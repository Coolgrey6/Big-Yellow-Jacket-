// src/components/Sidebar/Sidebar.tsx

import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Shield, Activity, Settings, Database, Network, AlertCircle, Radio } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <div className="w-64 bg-secondary-dark text-gray-300 h-screen">
      <nav className="p-4 space-y-6">
        <div className="pb-4 border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-green-500 animate-pulse" />
            <span className="text-sm text-gray-400">Monitoring Active</span>
          </div>
        </div>
        
        <ul className="space-y-2">
          <SidebarItem 
            icon={<Shield />} 
            text="Overview" 
            to="/"
            active={location.pathname === '/'} 
          />
          <SidebarItem 
            icon={<Activity />} 
            text="Monitoring" 
            to="/monitoring"
            active={location.pathname === '/monitoring'} 
          />
          <SidebarItem 
            icon={<Network />} 
            text="Connections" 
            to="/connections"
            active={location.pathname === '/connections'} 
          />
          <SidebarItem 
            icon={<AlertCircle />} 
            text="Alerts" 
            to="/alerts"
            active={location.pathname === '/alerts'} 
          />
          <SidebarItem 
            icon={<Database />} 
            text="Data" 
            to="/data"
            active={location.pathname === '/data'} 
          />
          <SidebarItem 
            icon={<Settings />} 
            text="Settings" 
            to="/settings"
            active={location.pathname === '/settings'} 
          />
        </ul>

        <div className="pt-4 border-t border-gray-700">
          <div className="text-sm text-gray-400">
            <p>System Status:</p>
            <p className="text-green-500">● Online</p>
          </div>
        </div>
      </nav>
    </div>
  );
};

interface SidebarItemProps {
  icon: React.ReactNode;
  text: string;
  to: string;
  active?: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon, text, to, active }) => (
  <Link to={to}>
    <li 
      className={`flex items-center space-x-3 p-2 rounded cursor-pointer transition-colors
        ${active 
          ? 'bg-primary text-secondary-dark' 
          : 'hover:bg-secondary-light text-gray-300'
        }`}
    >
      <span className={`${active ? 'text-secondary-dark' : 'text-gray-400'}`}>
        {icon}
      </span>
      <span>{text}</span>
    </li>
  </Link>
);