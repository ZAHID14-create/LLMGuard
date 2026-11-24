import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { Navbar } from '../components/Navbar';
import { useSystemHealth } from '../hooks/useSystemHealth';

export const DashboardLayout = () => {
  const healthState = useSystemHealth();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Workspace Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navbar */}
        <Navbar
          isConnected={healthState.isConnected}
          latency={healthState.latency}
          loading={healthState.loading}
          refresh={healthState.refresh}
          lastChecked={healthState.lastChecked}
        />

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet context={healthState} />
        </main>
      </div>
    </div>
  );
};
