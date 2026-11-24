import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  RefreshCw,
  Award,
  ShieldAlert,
  Activity,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Server,
  Zap,
  Clock,
  ExternalLink,
  Code2,
} from 'lucide-react';
import { getReportsSummary, exportReport } from '../services/api';

export const Reports = () => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('system'); // 'system' | 'evaluation' | 'safety' | 'observability'
  const [exportPreview, setExportPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewFormat, setPreviewFormat] = useState('markdown'); // 'markdown' | 'json' | 'csv'
  const [copied, setCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load summary
  const fetchSummaryData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    setErrorMsg(null);
    try {
      const data = await getReportsSummary();
      setSummary(data);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load system report summary');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Fetch report export preview
  const fetchExportPreview = useCallback(async (type, format) => {
    setPreviewLoading(true);
    setErrorMsg(null);
    try {
      const result = await exportReport({ type, format });
      setExportPreview(result);
    } catch (err) {
      setErrorMsg(err.message || `Failed to export ${type} report`);
    } finally {
      setPreviewLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummaryData();
  }, [fetchSummaryData]);

  useEffect(() => {
    fetchExportPreview(activeTab, previewFormat);
  }, [activeTab, previewFormat, fetchExportPreview]);

  // Handle client-side file download
  const handleDownload = () => {
    if (!exportPreview?.content) return;
    const mimeTypes = {
      markdown: 'text/markdown;charset=utf-8',
      json: 'application/json;charset=utf-8',
      csv: 'text/csv;charset=utf-8',
    };
    const mime = mimeTypes[exportPreview.format] || 'text/plain;charset=utf-8';
    const blob = new Blob([exportPreview.content], { type: mime });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = exportPreview.filename || `llmguard_${activeTab}_report.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleCopyContent = () => {
    if (!exportPreview?.content) return;
    navigator.clipboard.writeText(exportPreview.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // KPIs
  const totalRequests = summary?.llm_metrics?.total_requests ?? 0;
  const avgLatency = summary?.llm_metrics?.average_latency_ms ?? 0.0;
  const totalEvaluations = summary?.evaluation_summary?.total_evaluations ?? 0;
  const avgFaithfulness = summary?.evaluation_summary?.average_faithfulness ?? 0.0;
  const totalBlocked = summary?.guardrails_summary?.blocked_requests ?? 0;
  const totalChecked = summary?.guardrails_summary?.total_checked ?? 0;
  const totalTraces = summary?.observability_summary?.total_traces ?? 0;
  const totalTokens = summary?.observability_summary?.total_tokens_consumed ?? 0;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-950/70 border border-indigo-700/60 text-indigo-400">
              <FileText className="h-5 w-5" />
            </div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Reports &amp; Compliance History
              </h1>
            </div>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Cross-module platform auditing, evaluation scorecards, safety records, and export engine.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchSummaryData(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-700/80 bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700/80 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin text-indigo-400' : ''}`} />
            <span>Refresh Telemetry</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-lg border border-rose-800/60 bg-rose-950/40 p-4 text-xs text-rose-300 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {/* KPI Overview Grid */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold text-white tracking-tight">
          Executive Telemetry Summary
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-4 space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Inference Calls</span>
              <Server className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {totalRequests.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-400">
              Avg Latency: <strong className="text-amber-400 font-mono">{avgLatency} ms</strong>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-4 space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>DeepEval Evaluated</span>
              <Award className="h-4 w-4 text-violet-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {totalEvaluations.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-400">
              Avg Faithfulness: <strong className="text-violet-400 font-mono">{(avgFaithfulness * 100).toFixed(0)}%</strong>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-4 space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Threats Blocked</span>
              <ShieldAlert className="h-4 w-4 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {totalBlocked.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-400">
              Out of <strong className="text-slate-300 font-mono">{totalChecked}</strong> inspected
            </div>
          </div>

          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-4 space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Captured Traces</span>
              <Activity className="h-4 w-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {totalTraces.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-400">
              Tokens: <strong className="text-cyan-400 font-mono">{totalTokens.toLocaleString()}</strong>
            </div>
          </div>
        </div>
      </section>

      {/* Main Reporting Workspace */}
      <section className="space-y-4">
        {/* Navigation Tabs */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-2">
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'system', label: 'Platform Summary', icon: Layers },
              { id: 'evaluation', label: 'DeepEval Evaluation Report', icon: Award },
              { id: 'safety', label: 'Safety Guardrails Audit', icon: ShieldAlert },
              { id: 'observability', label: 'Langfuse Tracing Report', icon: Activity },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors ${
                    activeTab === tab.id
                      ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Format Selector Pills */}
          <div className="flex items-center space-x-1.5 rounded-lg border border-slate-800 bg-[#0c1220] p-1 text-xs">
            {['markdown', 'json', 'csv'].map((fmt) => (
              <button
                key={fmt}
                onClick={() => setPreviewFormat(fmt)}
                className={`rounded px-2.5 py-1 uppercase font-mono text-[11px] transition-colors ${
                  previewFormat === fmt
                    ? 'bg-indigo-600 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {fmt}
              </button>
            ))}
          </div>
        </div>

        {/* Export Action Card */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-800/90 bg-[#0d1424] p-4 gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-white capitalize">
                {activeTab} Report ({previewFormat.toUpperCase()})
              </span>
              <span className="font-mono text-[11px] text-slate-400">
                • Filename: <strong className="text-indigo-300">{exportPreview?.filename || 'loading...'}</strong>
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Generated from actual backend telemetry and database audit records.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyContent}
              disabled={!exportPreview?.content}
              className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-700/80 bg-slate-800/60 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700/80 transition-colors disabled:opacity-50"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>

            <button
              onClick={handleDownload}
              disabled={!exportPreview?.content}
              className="inline-flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors shadow-sm shadow-indigo-950 disabled:opacity-50"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download File</span>
            </button>
          </div>
        </div>

        {/* Live Report Content Preview Box */}
        <div className="rounded-xl border border-slate-800/90 bg-[#090d16] p-5 overflow-hidden">
          {previewLoading ? (
            <div className="py-16 text-center text-xs text-slate-400">
              <RefreshCw className="h-6 w-6 animate-spin text-indigo-400 mx-auto mb-2" />
              Generating {activeTab} report...
            </div>
          ) : !exportPreview?.content ? (
            <div className="py-16 text-center text-xs text-slate-400 space-y-2">
              <FileText className="h-8 w-8 text-slate-600 mx-auto" />
              <p className="text-slate-300 font-medium">No report content available</p>
              <p className="text-slate-500 max-w-sm mx-auto">
                Trigger queries in the AI Playground or run benchmark tests in LLM Evaluation to generate records.
              </p>
            </div>
          ) : (
            <div className="max-h-[550px] overflow-y-auto">
              <pre className="font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed select-text">
                {exportPreview.content}
              </pre>
            </div>
          )}
        </div>
      </section>

      {/* Compliance & Methodology Reference Card */}
      <section className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-3">
        <h3 className="text-sm font-semibold text-white">Evaluation &amp; Safety Compliance Standard</h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          LLMGuard implements strict separation between generation, evaluation, safety, and observability:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
          <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
            <span className="font-semibold text-violet-400">1. DeepEval Standards</span>
            <p className="text-[11px] text-slate-400">
              Faithfulness &ge; 70%, Relevancy &ge; 70%, Hallucination Agreement &ge; 70% (Risk &le; 30%). Tested across 28 reference cases.
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
            <span className="font-semibold text-cyan-400">2. Guardrails AI Shield</span>
            <p className="text-[11px] text-slate-400">
              Bidirectional inspection. Pre-call prompt neutralization and post-call PII/credential sanitization logged to SQLite.
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
            <span className="font-semibold text-amber-400">3. Langfuse Observability</span>
            <p className="text-[11px] text-slate-400">
              Telemetry captures latency, exact token usage, model identifiers, and error traces with privacy-safe redaction.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
