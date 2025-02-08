// src/App.tsx

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/Layout/AppLayout';
import { Dashboard } from './components/Dashboard/Dashboard';
import { Monitoring } from './components/Monitoring/Monitoring';
import { NetworkIntelligence } from './components/NetworkIntelligence/NetworkIntelligence';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="monitoring" element={<Monitoring />} />
          <Route path="connections" element={<NetworkIntelligence />} />
          <Route path="alerts" element={<div>Alerts Page</div>} />
          <Route path="data" element={<div>Data Page</div>} />
          <Route path="settings" element={<div>Settings Page</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;