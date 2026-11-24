import React from 'react';

export const MetricCard = ({ title, value, statusBadge, description, icon: Icon, accentColor = 'indigo' }) => {
  const accentStyles = {
    blue: 'text-blue-400 bg-blue-950/40 border-blue-800/60',
    violet: 'text-violet-400 bg-violet-950/40 border-violet-800/60',
    cyan: 'text-cyan-400 bg-cyan-950/40 border-cyan-800/60',
    amber: 'text-amber-400 bg-amber-950/40 border-amber-800/60',
    indigo: 'text-indigo-400 bg-indigo-950/40 border-indigo-800/60',
  };

  const style = accentStyles[accentColor] || accentStyles.indigo;

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 shadow-sm transition-all duration-200 hover:border-slate-700 hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</p>
          <h3 className="text-xl font-bold tracking-tight text-white">{value}</h3>
        </div>
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg border ${style}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3">
        <span className="rounded bg-slate-800/90 px-2 py-0.5 text-[11px] font-medium text-slate-300">
          {statusBadge}
        </span>
        <span className="text-[11px] text-slate-500 font-mono">{description}</span>
      </div>
    </div>
  );
};
