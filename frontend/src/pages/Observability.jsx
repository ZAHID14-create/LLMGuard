import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Zap,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Server,
  Cloud,
  CloudOff,
  RefreshCw,
  Search,
  Filter,
  Eye,
  X,
  ExternalLink,
  ChevronRight,
  Database,
  Terminal,
  Award,
  FileText,
} from 'lucide-react';
import {
  getObservabilitySummary,
  getObservabilityHistory,
  getObservabilityStatus,
} from '../services/api';

export const Observability = () => {
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [statusInfo, setStatusInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const fetchData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    setErrorMsg(null);
    try {
      const [sumData, histData, statData] = await Promise.all([
        getObservabilitySummary().catch(() => null),
        getObservabilityHistory({
          limit: 50,
          status: statusFilter === 'all' ? null : statusFilter,
        }).catch(() => ({ total: 0, traces: [] })),
        getObservabilityStatus().catch(() => null),
      ]);

      if (sumData) setSummary(sumData);
      if (histData) setHistory(histData.traces || []);
      if (statData) setStatusInfo(statData);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to fetch observability telemetry');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Derived metrics
  const totalTraces = summary?.total_traces ?? 0;
  const avgLatency = summary?.average_latency_ms ?? 0.0;
  const totalTokens = summary?.total_tokens_consumed ?? 0;
  const inputTokens = summary?.total_input_tokens ?? 0;
  const outputTokens = summary?.total_output_tokens ?? 0;
  const successfulReqs = summary?.successful_requests ?? 0;
  const failedReqs = summary?.failed_requests ?? 0;
  const connStatus = summary?.connection_status || statusInfo?.connection_status || 'Not Configured';

  const errorRate = totalTraces > 0 ? ((failedReqs / totalTraces) * 100).toFixed(1) : '0.0';

  // Calculate latency distributions from traces
  const latencyBuckets = {
    fast: history.filter((t) => t.latency_ms > 0 && t.latency_ms < 200).length,
    medium: history.filter((t) => t.latency_ms >= 200 && t.latency_ms < 600).length,
    slow: history.filter((t) => t.latency_ms >= 600).length,
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-950/60 border border-amber-800/60 text-amber-400">
              <Activity className="h-5 w-5" />
            </div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Observability &amp; Tracing
              </h1>
            </div>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            End-to-end LLM lifecycle tracing, latency profiling, and token analytics powered by Langfuse.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 rounded-lg border border-slate-800 bg-[#0c1220] px-3 py-1.5 text-xs font-medium">
            <span
              className={`h-2 w-2 rounded-full ${connStatus === 'Connected'
                  ? 'bg-emerald-400 ring-2 ring-emerald-500/20'
                  : connStatus === 'Not Configured'
                    ? 'bg-amber-400 ring-2 ring-amber-500/20'
                    : 'bg-rose-400 ring-2 ring-rose-500/20'
                }`}
            />
            <span className="text-slate-300">Langfuse:</span>
            <span
              className={`font-mono ${connStatus === 'Connected'
                  ? 'text-emerald-400'
                  : connStatus === 'Not Configured'
                    ? 'text-amber-400'
                    : 'text-rose-400'
                }`}
            >
              {connStatus}
            </span>
          </div>

          <Link
            to="/reports"
            className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-700/80 bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700/80 hover:text-white transition-colors"
          >
            <FileText className="h-3.5 w-3.5 text-amber-400" />
            <span>Export Traces</span>
          </Link>

          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-700/80 bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700/80 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin text-amber-400' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-lg border border-rose-800/60 bg-rose-950/40 p-4 text-xs text-rose-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-rose-200">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* SECTION 1: Key Telemetry Metrics Overview */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white tracking-tight">
            Telemetry Overview
          </h2>
          <span className="text-xs font-mono text-slate-400">
            Audit Store: SQLite ({summary?.local_only_traces ?? 0} local) + Langfuse ({summary?.cloud_synced_traces ?? 0} cloud)
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Total Traces */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Total Recorded Traces</span>
              <Activity className="h-4 w-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {totalTraces.toLocaleString()}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span className="text-emerald-400 font-mono">{successfulReqs} Success</span>
              <span className="text-rose-400 font-mono">{failedReqs} Errored/Blocked</span>
            </div>
          </div>

          {/* Average Latency */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Average Latency</span>
              <Clock className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {avgLatency > 0 ? `${avgLatency} ms` : '0 ms'}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span>Mean roundtrip execution</span>
              <span className="text-blue-400 font-mono">Gemini Profiler</span>
            </div>
          </div>

          {/* Total Tokens Consumed */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Total Tokens Consumed</span>
              <Zap className="h-4 w-4 text-violet-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {totalTokens.toLocaleString()}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span>{inputTokens.toLocaleString()} In</span>
              <span>{outputTokens.toLocaleString()} Out</span>
            </div>
          </div>

          {/* Error Rate */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Error &amp; Block Rate</span>
              <AlertTriangle className="h-4 w-4 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {errorRate}%
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span>Safety &amp; API issues</span>
              <span className="text-slate-300 font-mono">{failedReqs} incidents</span>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2 & 3: Latency Monitoring & Token Analytics */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Latency Distribution */}
        <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-white">Latency Performance Breakdown</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">{history.length} samples</span>
          </div>

          <div className="space-y-3">
            {/* Fast (<200ms) */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Fast (&lt; 200 ms)</span>
                <span className="font-mono text-emerald-400">
                  {latencyBuckets.fast} traces ({history.length > 0 ? ((latencyBuckets.fast / history.length) * 100).toFixed(0) : 0}%)
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                  style={{
                    width: `${history.length > 0 ? (latencyBuckets.fast / history.length) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>

            {/* Medium (200-600ms) */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Medium (200 - 600 ms)</span>
                <span className="font-mono text-amber-400">
                  {latencyBuckets.medium} traces ({history.length > 0 ? ((latencyBuckets.medium / history.length) * 100).toFixed(0) : 0}%)
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full transition-all duration-300"
                  style={{
                    width: `${history.length > 0 ? (latencyBuckets.medium / history.length) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>

            {/* Slow (>600ms) */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">High Latency (&gt; 600 ms)</span>
                <span className="font-mono text-rose-400">
                  {latencyBuckets.slow} traces ({history.length > 0 ? ((latencyBuckets.slow / history.length) * 100).toFixed(0) : 0}%)
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full transition-all duration-300"
                  style={{
                    width: `${history.length > 0 ? (latencyBuckets.slow / history.length) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
            <span>Target P95 Latency: &lt; 500 ms</span>
            <span className="text-slate-300">Average: <strong className="font-mono text-amber-400">{avgLatency} ms</strong></span>
          </div>
        </div>

        {/* Token Accounting & Model Breakdown */}
        <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="h-4 w-4 text-violet-400" />
              <h3 className="text-sm font-semibold text-white">Token Usage &amp; Cost Tracking</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">Actual Tokens</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400">Prompt / Input Tokens</span>
              <div className="text-lg font-bold font-mono text-violet-400">
                {inputTokens.toLocaleString()}
              </div>
              <span className="text-[10px] text-slate-500">
                {totalTokens > 0 ? `${((inputTokens / totalTokens) * 100).toFixed(0)}% of total` : '0%'}
              </span>
            </div>

            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400">Completion Tokens</span>
              <div className="text-lg font-bold font-mono text-cyan-400">
                {outputTokens.toLocaleString()}
              </div>
              <span className="text-[10px] text-slate-500">
                {totalTokens > 0 ? `${((outputTokens / totalTokens) * 100).toFixed(0)}% of total` : '0%'}
              </span>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800/70 bg-[#0c1220] p-3 text-xs space-y-1.5">
            <div className="flex justify-between items-center text-slate-300">
              <span className="flex items-center space-x-1.5">
                <Terminal className="h-3.5 w-3.5 text-indigo-400" />
                <span>Primary LLM Engine:</span>
              </span>
              <span className="font-mono text-indigo-300 font-semibold">gemini-2.5-flash</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Token usage is directly parsed from Google GenAI SDK <code className="text-slate-300">usage_metadata</code> and logged with trace IDs.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 4: Live Trace Explorer */}
      <section className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-white tracking-tight">
              Live Trace Explorer
            </h2>
            <p className="text-xs text-slate-400">
              Chronological execution waterfall of Gemini requests, safety guardrails, and DeepEval runs.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center space-x-1.5 rounded-lg border border-slate-800 bg-[#0c1220] p-1 text-xs">
            {['all', 'success', 'blocked', 'error', 'sanitized'].map((f) => (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`rounded-md px-2.5 py-1 capitalize transition-colors ${statusFilter === f
                    ? 'bg-amber-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                  }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Traces Table */}
        <div className="overflow-hidden rounded-xl border border-slate-800/90 bg-[#0d1424]">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400">
              <RefreshCw className="h-6 w-6 animate-spin text-amber-400 mx-auto mb-2" />
              Loading observability traces...
            </div>
          ) : history.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400 space-y-2">
              <Activity className="h-8 w-8 text-slate-600 mx-auto" />
              <p className="text-slate-300 font-medium">No execution traces recorded yet</p>
              <p className="text-slate-500 max-w-md mx-auto">
                Trigger queries in the AI Playground, evaluate responses with DeepEval, or test guardrails to capture live traces.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-800 bg-[#090d16] text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                  <tr>
                    <th className="py-3 px-4">Trace ID</th>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Operation</th>
                    <th className="py-3 px-4">Model</th>
                    <th className="py-3 px-4 text-right">Latency</th>
                    <th className="py-3 px-4 text-right">Tokens</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center">Sync</th>
                    <th className="py-3 px-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {history.map((t) => (
                    <tr
                      key={t.trace_id}
                      className="hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="py-3 px-4 text-indigo-400 font-semibold">
                        {t.trace_id.substring(0, 16)}...
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px] font-sans">
                        {new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </td>
                      <td className="py-3 px-4 text-slate-200 font-sans font-medium">
                        {t.name}
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        {t.model || '–'}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-200">
                        {t.latency_ms > 0 ? `${t.latency_ms.toFixed(1)} ms` : '–'}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300">
                        {t.total_tokens !== null ? t.total_tokens : '–'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium font-sans ${t.status === 'success' || t.status === 'passed'
                              ? 'bg-emerald-950/60 border border-emerald-800/60 text-emerald-400'
                              : t.status === 'blocked'
                                ? 'bg-amber-950/60 border border-amber-800/60 text-amber-400'
                                : t.status === 'sanitized'
                                  ? 'bg-cyan-950/60 border border-cyan-800/60 text-cyan-400'
                                  : 'bg-rose-950/60 border border-rose-800/60 text-rose-400'
                            }`}
                        >
                          {t.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {t.is_remote ? (
                          <span className="inline-flex items-center text-emerald-400" title="Synced to Langfuse Cloud">
                            <Cloud className="h-3.5 w-3.5" />
                          </span>
                        ) : (
                          <span className="inline-flex items-center text-slate-500" title="Stored in Local SQLite Audit">
                            <Database className="h-3.5 w-3.5" />
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        <button
                          onClick={() => setSelectedTrace(t)}
                          className="inline-flex items-center space-x-1 rounded bg-slate-800/80 px-2 py-1 text-[11px] text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                        >
                          <Eye className="h-3 w-3" />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* SECTION 5 & 6: Incident Breakdown & Langfuse Connection Card */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Safety & Failure Breakdown */}
        <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-4">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">Safety &amp; Error Monitoring</h3>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
              <span className="text-slate-400">Total Failed / Intercepted Executions</span>
              <span className="font-mono font-semibold text-rose-400">{failedReqs}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
              <span className="text-slate-400">Guardrail Threat Interceptions</span>
              <span className="font-mono text-amber-400">
                {history.filter((t) => t.status === 'blocked').length}
              </span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
              <span className="text-slate-400">PII &amp; Credential Sanitizations</span>
              <span className="font-mono text-cyan-400">
                {history.filter((t) => t.status === 'sanitized').length}
              </span>
            </div>
            <div className="flex justify-between items-center py-1.5">
              <span className="text-slate-400">API &amp; System Exceptions</span>
              <span className="font-mono text-rose-400">
                {history.filter((t) => t.status === 'error').length}
              </span>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 text-[11px] text-slate-400 leading-relaxed">
            Privacy Guarantee: API keys, authentication credentials, and raw PII are strictly redacted prior to trace storage or remote dispatch.
          </div>
        </div>

        {/* Langfuse Cloud Connection Card & Guidance */}
        <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Cloud className="h-4 w-4 text-amber-400" />
              <h3 className="text-sm font-semibold text-white">Langfuse Cloud Configuration</h3>
            </div>
            <a
              href="https://cloud.langfuse.com"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center space-x-1 text-xs text-amber-400 hover:text-amber-300"
            >
              <span>cloud.langfuse.com</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Connection State</span>
              <span
                className={`font-mono font-medium ${connStatus === 'Connected'
                    ? 'text-emerald-400'
                    : connStatus === 'Not Configured'
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }`}
              >
                {connStatus}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Langfuse Base URL</span>
              <span className="font-mono text-slate-300">
                {statusInfo?.base_url || 'https://cloud.langfuse.com'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Official Python SDK</span>
              <span className="font-mono text-slate-300">langfuse v5.2.0</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Local Telemetry Fallback</span>
              <span className="font-mono text-emerald-400">Active (SQLite)</span>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 text-[11px] text-slate-400 space-y-1.5">
            <span className="font-semibold text-slate-300">Cloud Synchronization:</span>
            <p className="leading-relaxed">
              Production telemetry traces and execution spans stream to Langfuse Cloud for real-time observability, latency profiling, and cost tracking.
            </p>
          </div>
        </div>
      </section>

      {/* INSPECT TRACE MODAL */}
      {selectedTrace && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-2xl rounded-2xl border border-slate-800 bg-[#0d1424] p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-amber-400" />
                <h3 className="text-base font-bold text-white">Trace Metadata Inspector</h3>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
                  <span className="text-slate-500">Trace ID</span>
                  <div className="font-mono text-indigo-400 select-all font-semibold break-all">
                    {selectedTrace.trace_id}
                  </div>
                </div>
                <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
                  <span className="text-slate-500">Execution Status</span>
                  <div>
                    <span className="font-mono font-semibold text-amber-400 capitalize">
                      {selectedTrace.status}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
                  <span className="text-slate-500">Model</span>
                  <div className="font-mono text-slate-200">
                    {selectedTrace.model || '–'}
                  </div>
                </div>
                <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
                  <span className="text-slate-500">Latency</span>
                  <div className="font-mono text-slate-200">
                    {selectedTrace.latency_ms > 0 ? `${selectedTrace.latency_ms.toFixed(2)} ms` : '0 ms'}
                  </div>
                </div>
                <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
                  <span className="text-slate-500">Total Tokens</span>
                  <div className="font-mono text-slate-200">
                    {selectedTrace.total_tokens !== null ? selectedTrace.total_tokens : '–'}
                  </div>
                </div>
              </div>

              {selectedTrace.guardrail_status && (
                <div className="rounded-lg border border-amber-900/40 bg-amber-950/20 p-3 space-y-1">
                  <span className="text-amber-400 font-semibold">Guardrails AI Decision</span>
                  <p className="text-slate-300">
                    Status: <strong className="font-mono">{selectedTrace.guardrail_status}</strong>
                    {selectedTrace.risk_category && ` • Threat: ${selectedTrace.risk_category}`}
                  </p>
                </div>
              )}

              {selectedTrace.eval_metric && (
                <div className="rounded-lg border border-violet-900/40 bg-violet-950/20 p-3 space-y-1">
                  <span className="text-violet-400 font-semibold">DeepEval Metric</span>
                  <p className="text-slate-300">
                    Metric: <strong className="font-mono">{selectedTrace.eval_metric}</strong> • Score: <strong className="font-mono text-emerald-400">{selectedTrace.eval_score}</strong>
                  </p>
                </div>
              )}

              {selectedTrace.error_message && (
                <div className="rounded-lg border border-rose-900/40 bg-rose-950/20 p-3 space-y-1">
                  <span className="text-rose-400 font-semibold">
                    Error ({selectedTrace.error_type || 'Exception'})
                  </span>
                  <p className="font-mono text-rose-300 break-words">
                    {selectedTrace.error_message}
                  </p>
                </div>
              )}

              <div className="flex justify-between items-center pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                <span>Timestamp: {new Date(selectedTrace.timestamp).toLocaleString()}</span>
                <span>
                  Storage: {selectedTrace.is_remote ? 'Synced to Langfuse Cloud' : 'Local SQLite Audit Record'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
