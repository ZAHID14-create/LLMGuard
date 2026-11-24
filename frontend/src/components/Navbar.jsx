import React from 'react';
import { useLocation } from 'react-router-dom';
import { RefreshCw, Server, Wifi, WifiOff } from 'lucide-react';

const routeTitles = {
  '/': { title: 'Platform Overview', subtitle: 'System health, architecture roadmap, and core metrics' },
  '/playground': { title: 'AI Playground', subtitle: 'Interactive prompt testing and Gemini LLM response generation' },
  '/evaluation': { title: 'LLM Evaluation', subtitle: 'DeepEval automated evaluation metrics and benchmarks' },
  '/guardrails': { title: 'Safety Guardrails', subtitle: 'Real-time Guardrails AI validation and moderation rules' },
  '/observability': { title: 'Observability & Tracing', subtitle: 'Langfuse execution traces, latency tracking, and cost analytics' },
  '/reports': { title: 'Reports & History', subtitle: 'Exportable evaluation logs and audit history' },
};

export const Navbar = ({ isConnected, latency, loading, refresh, lastChecked }) => {
  const location = useLocation();
  const currentInfo = routeTitles[location.pathname] || {
    title: 'LLMGuard Platform',
    subtitle: 'AI Engineering Evaluation & Monitoring',
  };

  return (
    <header className="sticky top-0 z-10 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-[#0c1220]/90 px-6 backdrop-blur-md">
      {/* Route Title & Breadcrumb */}
      <div>
        <h1 className="text-base font-semibold text-white tracking-tight">{currentInfo.title}</h1>
        <p className="text-xs text-slate-400 hidden sm:block">{currentInfo.subtitle}</p>
      </div>

      {/* Right Controls: Connectivity Pulse & Refresh */}
      <div className="flex items-center space-x-3">
        {/* Backend Connectivity Status Pill */}
        <div
          className={`flex items-center space-x-2 rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
            isConnected
              ? 'bg-emerald-950/60 border-emerald-800/80 text-emerald-400'
              : 'bg-rose-950/60 border-rose-800/80 text-rose-400'
          }`}
        >
          <span className="relative flex h-2 w-2">
            {isConnected && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isConnected ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            ></span>
          </span>
          <span className="flex items-center space-x-1">
            {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            <span>{isConnected ? `Backend Connected` : `Backend Offline`}</span>
            {isConnected && latency !== null && (
              <span className="text-[10px] text-emerald-300 font-mono">({latency}ms)</span>
            )}
          </span>
        </div>

        {/* Check / Refresh Button */}
        <button
          onClick={refresh}
          disabled={loading}
          className="flex items-center space-x-1.5 rounded-lg border border-slate-700/80 bg-slate-800/60 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-all disabled:opacity-50"
          title="Manually ping backend API"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>

        {/* API Docs Button */}
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center space-x-1 rounded-lg border border-indigo-500/30 bg-indigo-950/40 px-2.5 py-1.5 text-xs font-medium text-indigo-300 hover:bg-indigo-900/60 transition-colors"
        >
          <Server className="h-3.5 w-3.5 text-indigo-400" />
          <span className="hidden sm:inline">Swagger Docs</span>
        </a>
      </div>
    </header>
  );
};
