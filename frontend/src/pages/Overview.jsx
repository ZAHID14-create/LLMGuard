import React from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  MessageSquare,
  Award,
  ShieldAlert,
  Clock,
  Server,
  MonitorCheck,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Layers,
  ArrowRight,
  BarChart3,
  Cpu,
  Zap,
  Activity,
  FileText,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

export const Overview = () => {
  const {
    isConnected,
    latency,
    backendData,
    projectInfo,
    metrics,
    evalSummary,
    guardrailsSummary,
    observabilitySummary,
    loading,
    error,
    refresh,
  } = useOutletContext();

  // Inference & Token metrics
  const totalRequests = observabilitySummary?.total_llm_requests ?? metrics?.total_requests ?? 0;
  const averageLatency = observabilitySummary?.average_latency_ms || metrics?.average_latency_ms || 0.0;
  const promptTokens = observabilitySummary?.total_input_tokens ?? 0;
  const completionTokens = observabilitySummary?.total_output_tokens ?? 0;
  const totalTokens = observabilitySummary?.total_tokens_consumed || metrics?.total_tokens || 0;

  // Evaluation metrics
  const totalEvaluations = evalSummary?.total_evaluations ?? 0;
  const avgFaithfulness = evalSummary?.average_faithfulness ?? null;
  const avgRelevancy = evalSummary?.average_answer_relevancy ?? null;
  const avgHallucinationScore = evalSummary?.average_hallucination_score ?? null; // Factual agreement
  const avgHallucinationRisk = evalSummary?.average_hallucination_risk ?? null; // Probability of hallucination
  const isApiConfigured = evalSummary?.api_configured ?? false;

  // Guardrail metrics
  const totalChecked = guardrailsSummary?.total_checked ?? 0;
  const totalBlocked = guardrailsSummary?.blocked_requests ?? 0;
  const totalRedacted = guardrailsSummary?.redacted_requests ?? 0;

  // Observability metrics
  const totalTraces = observabilitySummary?.total_traces ?? 0;
  const successfulRequests = observabilitySummary?.successful_requests ?? 0;
  const failedRequests = observabilitySummary?.failed_requests ?? 0;
  const obsConnectionStatus = observabilitySummary?.connection_status ?? 'Not Configured';

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {/* Hero Welcome Header */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-800/90 bg-gradient-to-r from-[#0d1424] via-[#0f172a] to-[#121c33] p-6 md:p-8">
        <div className="relative z-10 max-w-3xl space-y-3">
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
            LLMGuard – AI Evaluation &amp; Safety Monitoring Platform
          </h1>
          <p className="text-sm md:text-base leading-relaxed text-slate-300">
            A unified, enterprise-grade AI monitoring platform that evaluates Large Language Model outputs,
            enforces bidirectional safety guardrails, and captures production telemetry.
            All six application modules are fully integrated into one seamless workflow.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-2.5">
            <Link
              to="/playground"
              className="inline-flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors shadow-sm shadow-indigo-950"
            >
              <MessageSquare className="h-3.5 w-3.5" />
              <span>AI Playground</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
            <Link
              to="/evaluation"
              className="inline-flex items-center space-x-1.5 rounded-lg border border-violet-500/40 bg-violet-950/40 px-3.5 py-2 text-xs font-semibold text-violet-300 hover:bg-violet-900/60 transition-colors"
            >
              <Award className="h-3.5 w-3.5 text-violet-400" />
              <span>DeepEval Evaluation</span>
            </Link>
            <Link
              to="/guardrails"
              className="inline-flex items-center space-x-1.5 rounded-lg border border-cyan-500/40 bg-cyan-950/40 px-3.5 py-2 text-xs font-semibold text-cyan-300 hover:bg-cyan-900/60 transition-colors"
            >
              <ShieldAlert className="h-3.5 w-3.5 text-cyan-400" />
              <span>Safety Guardrails</span>
            </Link>
            <Link
              to="/observability"
              className="inline-flex items-center space-x-1.5 rounded-lg border border-amber-500/40 bg-amber-950/40 px-3.5 py-2 text-xs font-semibold text-amber-300 hover:bg-amber-900/60 transition-colors"
            >
              <Activity className="h-3.5 w-3.5 text-amber-400" />
              <span>Langfuse Observability</span>
            </Link>
            <Link
              to="/reports"
              className="inline-flex items-center space-x-1.5 rounded-lg border border-emerald-500/40 bg-emerald-950/40 px-3.5 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/60 transition-colors"
            >
              <FileText className="h-3.5 w-3.5 text-emerald-400" />
              <span>Reports &amp; Export</span>
            </Link>
          </div>
        </div>

        {/* Decorative ambient gradients */}
        <div className="pointer-events-none absolute -right-10 -top-10 h-64 w-64 rounded-full bg-indigo-600/10 blur-3xl" />
        <div className="pointer-events-none absolute right-40 -bottom-10 h-48 w-48 rounded-full bg-emerald-600/10 blur-2xl" />
      </div>

      {/* SECTION 1: Core Inference & Traffic Telemetry */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white tracking-tight">
              Inference &amp; Request Telemetry
            </h2>
            <p className="text-xs text-slate-400">
              Live operational metrics recorded from actual Gemini API calls and trace pipelines.
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
            <Zap className="h-3.5 w-3.5 text-amber-400" />
            <span>Total Tokens: <strong className="text-slate-200">{totalTokens.toLocaleString()}</strong></span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            to="/playground"
            className="group rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2 hover:border-indigo-500/40 transition-colors"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Total LLM Requests</span>
              <MessageSquare className="h-4 w-4 text-blue-400 group-hover:text-indigo-400 transition-colors" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {totalRequests.toLocaleString()}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span className="text-emerald-400 font-mono">{successfulRequests} Successful</span>
              <span className="text-rose-400 font-mono">{failedRequests} Failed</span>
            </div>
          </Link>

          <Link
            to="/observability"
            className="group rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2 hover:border-amber-500/40 transition-colors"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Average Latency</span>
              <Clock className="h-4 w-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {averageLatency > 0 ? `${averageLatency} ms` : '0 ms'}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span>Target: &lt; 500 ms</span>
              <span className="text-amber-400 font-mono">P95 Monitored</span>
            </div>
          </Link>

          <Link
            to="/observability"
            className="group rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2 hover:border-violet-500/40 transition-colors"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Prompt Tokens</span>
              <Zap className="h-4 w-4 text-violet-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {promptTokens.toLocaleString()}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span>Input Tokens</span>
              <span className="text-violet-400 font-mono">usage_metadata</span>
            </div>
          </Link>

          <Link
            to="/observability"
            className="group rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2 hover:border-cyan-500/40 transition-colors"
          >
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Completion Tokens</span>
              <Cpu className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {completionTokens.toLocaleString()}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
              <span>Output Tokens</span>
              <span className="text-cyan-400 font-mono">Generated Output</span>
            </div>
          </Link>
        </div>
      </section>

      {/* SECTION 2: DeepEval LLM Evaluation & Safety Metrics */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* DeepEval Evaluation Summary Card */}
        <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2">
              <Award className="h-5 w-5 text-violet-400" />
              <h3 className="text-sm font-semibold text-white">DeepEval LLM Evaluation</h3>
            </div>
            <Link
              to="/evaluation"
              className="text-xs text-violet-400 hover:text-violet-300 font-medium inline-flex items-center space-x-1"
            >
              <span>Scorecards</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400 font-medium">Faithfulness</span>
              <div className="text-lg font-bold font-mono text-violet-400">
                {avgFaithfulness !== null ? `${(avgFaithfulness * 100).toFixed(0)}%` : 'Not Available'}
              </div>
              <span className="text-[10px] text-slate-500">Threshold: &ge; 70%</span>
            </div>

            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400 font-medium">Answer Relevancy</span>
              <div className="text-lg font-bold font-mono text-indigo-400">
                {avgRelevancy !== null ? `${(avgRelevancy * 100).toFixed(0)}%` : 'Not Available'}
              </div>
              <span className="text-[10px] text-slate-500">Threshold: &ge; 70%</span>
            </div>

            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400 font-medium">Factual Agreement</span>
              <div className="text-lg font-bold font-mono text-cyan-400">
                {avgHallucinationScore !== null ? `${(avgHallucinationScore * 100).toFixed(0)}%` : 'Not Available'}
              </div>
              <span className="text-[10px] text-slate-500">Score &ge; 70%</span>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-[#0c1220] p-3 text-xs space-y-1.5">
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Hallucination Risk (1.0 - Agreement):</span>
              <span className="font-mono text-amber-400 font-semibold">
                {avgHallucinationRisk !== null ? `${(avgHallucinationRisk * 100).toFixed(1)}%` : 'Not Available'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              <strong>Metric Definition:</strong> Faithfulness verifies whether assertions are supported by context. Hallucination Score measures factual agreement rate (higher is better; risk is the inverted probability of ungrounded output).
            </p>
          </div>
        </div>

        {/* Safety Guardrails & Threat Interception Card */}
        <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="h-5 w-5 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">Guardrails AI Safety Shield</h3>
            </div>
            <Link
              to="/guardrails"
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center space-x-1"
            >
              <span>Audit History</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400 font-medium">Inspected</span>
              <div className="text-lg font-bold font-mono text-white">
                {totalChecked.toLocaleString()}
              </div>
              <span className="text-[10px] text-slate-500">Prompts &amp; Outputs</span>
            </div>

            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400 font-medium">Blocked</span>
              <div className="text-lg font-bold font-mono text-rose-400">
                {totalBlocked.toLocaleString()}
              </div>
              <span className="text-[10px] text-rose-500/80">Threats Prevented</span>
            </div>

            <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 space-y-1">
              <span className="text-slate-400 font-medium">Sanitized</span>
              <div className="text-lg font-bold font-mono text-cyan-400">
                {totalRedacted.toLocaleString()}
              </div>
              <span className="text-[10px] text-cyan-500/80">PII / Keys Redacted</span>
            </div>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-[#0c1220] p-3 text-xs space-y-1.5">
            <div className="flex justify-between items-center text-slate-300">
              <span className="text-slate-400">Audit Storage:</span>
              <span className="font-mono text-emerald-400">SQLite (safety_logs.db)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              <strong>Safety Coverage:</strong> Prompt injection detection, DAN jailbreak persona prevention, toxicity filtering, and automated credential masking (<code className="text-slate-300">[REDACTED_API_KEY]</code>, <code className="text-slate-300">[REDACTED_EMAIL]</code>).
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 3: System Status, Connectivity & Telemetry State */}
      <section className="space-y-4">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight">
            System Subsystems &amp; Connectivity Status
          </h2>
          <p className="text-xs text-slate-400">
            Real-time diagnostics across FastAPI ASGI server, DeepEval engine, Guardrails AI, and Langfuse Cloud.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Frontend Status */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm font-semibold text-white">
                <MonitorCheck className="h-4 w-4 text-cyan-400" />
                <span>React Frontend</span>
              </div>
              <span className="inline-flex items-center rounded-full bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 text-[11px] font-medium text-emerald-400">
                Active
              </span>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Framework</span>
                <span className="font-mono text-slate-200">React 19 + Vite 8</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Theme</span>
                <span className="font-mono text-slate-200">Dark Tailwind CSS v4</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Modules Active</span>
                <span className="font-mono text-emerald-400">6 Subsystems</span>
              </div>
            </div>
          </div>

          {/* Backend Status */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm font-semibold text-white">
                <Server className="h-4 w-4 text-indigo-400" />
                <span>FastAPI Backend</span>
              </div>
              <span
                className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${isConnected
                    ? 'bg-emerald-950/60 border-emerald-800/60 text-emerald-400'
                    : 'bg-rose-950/60 border-rose-800/60 text-rose-400'
                  }`}
              >
                {isConnected ? 'Healthy / Online' : 'Offline / Unreachable'}
              </span>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">API Version</span>
                <span className="font-mono text-slate-200">{backendData?.version || '0.6.0'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Environment</span>
                <span className="font-mono text-slate-200">development</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Inference Engine</span>
                <span className="font-mono text-slate-200">Google GenAI SDK</span>
              </div>
            </div>
          </div>

          {/* Langfuse Telemetry Status */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm font-semibold text-white">
                <Activity className="h-4 w-4 text-amber-400" />
                <span>Langfuse Telemetry</span>
              </div>
              <span
                className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${obsConnectionStatus === 'Connected'
                    ? 'bg-emerald-950/60 border-emerald-800/60 text-emerald-400'
                    : obsConnectionStatus === 'Not Configured'
                      ? 'bg-amber-950/60 border-amber-800/60 text-amber-400'
                      : 'bg-rose-950/60 border-rose-800/60 text-rose-400'
                  }`}
              >
                {obsConnectionStatus}
              </span>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Total Traces Captured</span>
                <span className="font-mono text-slate-200">{totalTraces}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Official SDK</span>
                <span className="font-mono text-slate-200">langfuse v5.2.0</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Local Telemetry Fallback</span>
                <span className="font-mono text-emerald-400">Active (SQLite)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: Architecture Roadmap (All 6 Phases Integrated) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white tracking-tight">
              Integrated Architectural Subsystems
            </h2>
            <p className="text-xs text-slate-400">
              Complete multi-phase engineering pipeline deployed in LLMGuard.
            </p>
          </div>
          <Link
            to="/reports"
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center space-x-1"
          >
            <span>Export Full Audit Report</span>
            <ExternalLink className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[
            {
              id: 'foundation',
              title: 'Full-Stack Foundation',
              tool: 'FastAPI + Vite',
              icon: Server,
              desc: 'Async ASGI backend, REST routing, CORS security, and dark-themed React dashboard.',
              status: 'Operational',
              path: '/',
            },
            {
              id: 'inference',
              title: 'LLM Response Generation',
              tool: 'Google GenAI SDK',
              icon: MessageSquare,
              desc: 'High-speed Gemini inference with multi-turn context and token profiling.',
              status: 'Operational',
              path: '/playground',
            },
            {
              id: 'evaluation',
              title: 'Automated LLM Evaluation',
              tool: 'DeepEval',
              icon: Award,
              desc: 'Evaluation testing for Faithfulness, Answer Relevancy, and Hallucination metrics.',
              status: 'Operational',
              path: '/evaluation',
            },
            {
              id: 'guardrails',
              title: 'Safety Guardrails Shield',
              tool: 'Guardrails AI',
              icon: ShieldAlert,
              desc: 'Bidirectional prompt injection, jailbreak defense, toxicity, and PII redaction.',
              status: 'Operational',
              path: '/guardrails',
            },
            {
              id: 'observability',
              title: 'Observability & Tracing',
              tool: 'Langfuse v5.2',
              icon: Activity,
              desc: 'Full-lifecycle execution tracing, latency profiling, token metrics, and local fallback.',
              status: 'Operational',
              path: '/observability',
            },
            {
              id: 'reports',
              title: 'Reports & Compliance History',
              tool: 'Multi-Format Export',
              icon: FileText,
              desc: 'Cross-module telemetry summaries, Markdown/JSON/CSV exports, and audit history.',
              status: 'Operational',
              path: '/reports',
            },
          ].map((item) => {
            const ItemIcon = item.icon;
            return (
              <Link
                key={item.id}
                to={item.path}
                className="group rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-950/60 border border-indigo-800/50 text-indigo-400">
                      <ItemIcon className="h-4 w-4" />
                    </div>
                    <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">
                      {item.title}
                    </h3>
                  </div>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                    {item.tool}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px]">
                  <span className="text-slate-400">Subsystem: <strong className="text-slate-300">{item.tool}</strong></span>
                  <span className="font-mono text-emerald-400 font-medium">{item.status}</span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
};
