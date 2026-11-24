import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  Terminal,
  CheckCircle2,
  Lock,
  Activity,
  FileText,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

const navigationItems = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'AI Playground', path: '/playground', icon: Terminal },
  { name: 'LLM Evaluation', path: '/evaluation', icon: CheckCircle2 },
  { name: 'Safety Guardrails', path: '/guardrails', icon: Lock },
  { name: 'Observability', path: '/observability', icon: Activity },
  { name: 'Reports & History', path: '/reports', icon: FileText },
];

export const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`relative flex flex-col border-r border-slate-800/80 bg-[#0c1220] transition-all duration-300 ease-in-out z-20 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-500/20">
            <ShieldAlert className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-white text-lg">LLMGuard</span>
              <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">
                AI Safety & Eval
              </span>
            </div>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden md:flex h-7 w-7 items-center justify-center rounded-lg border border-slate-700/60 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
        <div className={`px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400 ${collapsed ? 'text-center' : ''}`}>
          {collapsed ? '•••' : 'Platform Modules'}
        </div>
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm shadow-indigo-950'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                } ${collapsed ? 'justify-center' : 'justify-between'}`
              }
            >
              <div className="flex items-center space-x-3 min-w-0">
                <Icon className="h-5 w-5 shrink-0 transition-colors group-hover:text-indigo-400" />
                {!collapsed && <span className="truncate">{item.name}</span>}
              </div>
            </NavLink>
          );
        })}
      </nav>

      {/* Sidebar Footer Info */}
      <div className="border-t border-slate-800/80 p-3 bg-slate-900/40">
        {!collapsed ? (
          <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 text-xs">
            <div className="flex items-center space-x-2 text-indigo-400 font-semibold mb-1">
              <Sparkles className="h-3.5 w-3.5" />
              <span>LLMGuard Engine</span>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              DeepEval + Guardrails + Langfuse <br />
              <span className="text-emerald-400 font-mono">v0.8.0 • Production</span>
            </p>
          </div>
        ) : (
          <div className="flex justify-center text-emerald-400" title="LLMGuard v0.8.0">
            <Sparkles className="h-5 w-5" />
          </div>
        )}
      </div>
    </aside>
  );
};
