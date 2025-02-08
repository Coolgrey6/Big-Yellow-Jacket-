import React from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { NetworkIntelligence } from './components/NetworkIntelligence';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 bg-gray-50">
          <Dashboard />
          <NetworkIntelligence />
        </main>
      </div>
    </div>
  );
};

export default App;