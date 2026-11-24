import React, { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCcw,
  Layers,
  Award,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Clock,
  Sparkles,
  Filter,
  FileText,
  ChevronDown,
  ChevronUp,
  Cpu,
  BarChart3,
  ExternalLink,
} from 'lucide-react';
import { evaluateResponse, runBenchmark, getEvaluationHistory, getEvaluationSummary } from '../services/api';

const SAMPLE_BENCHMARK_PROMPTS = [
  {
    category: 'Computer Science',
    question: 'Explain the difference between a process and a thread in modern operating systems.',
    actual_response:
      'A process is an executing instance of a program with its own isolated address space, while a thread is a lightweight unit of execution within a process that shares memory with sibling threads.',
    reference_context:
      'In operating systems, a process is an instance of a computer program that is being executed, containing program code and its own isolated virtual address space. Threads are subsets of a process that share the parent process memory, file descriptors, and state, but have their own thread ID, program counter, registers, and call stack.',
    expected_output:
      'Processes have isolated virtual memory spaces, while threads share the address space of their parent process.',
  },
  {
    category: 'Science & Technology',
    question: 'What is CRISPR-Cas9 and how does it function in genetic engineering?',
    actual_response:
      'CRISPR-Cas9 uses a guide RNA to direct the Cas9 endonuclease enzyme to cleave targeted double-stranded DNA sequences for precise genome editing.',
    reference_context:
      'CRISPR-Cas9 is adapted from a natural prokaryotic antiviral defense system. It consists of two components: a guide RNA (gRNA) complementary to a target genomic locus and a Cas9 endonuclease enzyme. The gRNA guides Cas9 to the matching DNA sequence, where Cas9 cleaves both strands, triggering cellular repair mechanisms that can disable or modify genes.',
    expected_output:
      'CRISPR-Cas9 employs a guide RNA to direct Cas9 endonuclease to cut DNA at specific loci for targeted gene modification.',
  },
  {
    category: 'Incorrect / Unsupported Claims',
    question: 'Who was the first person to walk on Mars and in what year?',
    actual_response:
      'Astronaut Neil Armstrong walked on Mars in 1969 as part of the Apollo 11 mission.',
    reference_context:
      'As of 2026, no human has traveled to or landed on Mars. All successful missions to the Martian surface have been robotic probes, landers, and rovers (such as Curiosity and Perseverance) operated by space agencies like NASA.',
    expected_output:
      'No human has ever walked on Mars; only robotic rovers have explored the Martian surface.',
  },
];

export const Evaluation = () => {
  const { isConnected, evalSummary: globalEvalSummary, refresh } = useOutletContext();

  const [activeTab, setActiveTab] = useState('individual'); // 'individual' | 'benchmark' | 'history'
  const [evalSummary, setEvalSummary] = useState(globalEvalSummary);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyFilter, setHistoryFilter] = useState({ status: '', category: '' });

  // Individual evaluation form state
  const [individualForm, setIndividualForm] = useState({
    question: '',
    actual_response: '',
    reference_context: '',
    expected_output: '',
    category: 'Computer Science',
  });
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [latestResult, setLatestResult] = useState(null);
  const [evalError, setEvalError] = useState(null);

  // Benchmark runner state
  const [benchmarkSampleSize, setBenchmarkSampleSize] = useState(5);
  const [isBenchmarking, setIsBenchmarking] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [benchmarkError, setBenchmarkError] = useState(null);

  // Load summary and history
  const loadSummaryAndHistory = async () => {
    try {
      const [summaryData, historyData] = await Promise.all([
        getEvaluationSummary().catch(() => null),
        getEvaluationHistory({ limit: 30 }).catch(() => []),
      ]);
      if (summaryData) setEvalSummary(summaryData);
      if (historyData) setHistory(historyData);
    } catch (err) {
      console.error('Failed to load evaluation records:', err);
    }
  };

  useEffect(() => {
    loadSummaryAndHistory();
  }, []);

  const handleFillSample = (sample) => {
    setIndividualForm({
      question: sample.question,
      actual_response: sample.actual_response,
      reference_context: sample.reference_context,
      expected_output: sample.expected_output,
      category: sample.category,
    });
    setLatestResult(null);
    setEvalError(null);
  };

  const handleRunIndividualEvaluation = async (e) => {
    e.preventDefault();
    if (!individualForm.question.trim() || !individualForm.actual_response.trim() || !individualForm.reference_context.trim()) {
      setEvalError('Question, Actual Response, and Reference Context are all required fields.');
      return;
    }

    setIsEvaluating(true);
    setEvalError(null);
    try {
      const result = await evaluateResponse({
        question: individualForm.question.trim(),
        actual_response: individualForm.actual_response.trim(),
        reference_context: individualForm.reference_context.trim(),
        expected_output: individualForm.expected_output.trim() || null,
        category: individualForm.category,
      });
      setLatestResult(result);
      loadSummaryAndHistory();
    } catch (err) {
      setEvalError(err.message || 'Evaluation failed.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleRunBenchmark = async () => {
    setIsBenchmarking(true);
    setBenchmarkError(null);
    try {
      const summary = await runBenchmark({ sample_size: benchmarkSampleSize });
      setBenchmarkResult(summary);
      loadSummaryAndHistory();
    } catch (err) {
      setBenchmarkError(err.message || 'Benchmark evaluation failed.');
    } finally {
      setIsBenchmarking(false);
    }
  };

  const isApiConfigured = evalSummary?.api_configured ?? false;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-800/90 bg-gradient-to-r from-[#0d1424] via-[#0f172a] to-[#131b2e] p-6 md:p-8">
        <div className="relative z-10 max-w-3xl space-y-3">
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
            LLM Evaluation &amp; Benchmarking
          </h2>
          <p className="text-sm md:text-base leading-relaxed text-slate-300">
            Quantify AI response reliability with automated DeepEval metrics—evaluating{' '}
            <strong className="text-violet-300 font-semibold">Faithfulness</strong>,{' '}
            <strong className="text-indigo-300 font-semibold">Answer Relevancy</strong>, and{' '}
            <strong className="text-cyan-300 font-semibold">Hallucination Risk</strong> using Google Gemini as an LLM evaluation judge.
          </p>
        </div>

        {/* Decorative backdrop */}
        <div className="pointer-events-none absolute -right-10 -top-10 h-64 w-64 rounded-full bg-violet-600/10 blur-3xl" />
        <div className="pointer-events-none absolute right-40 -bottom-10 h-48 w-48 rounded-full bg-indigo-600/10 blur-2xl" />
      </div>

      {/* Section A: Evaluation Overview (Non-fabricated actual statistics) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white tracking-tight">Evaluation Metric Telemetry</h3>
            <p className="text-xs text-slate-400">
              Aggregate statistics calculated from recorded DeepEval evaluation runs.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Link
              to="/reports"
              className="inline-flex items-center space-x-1.5 rounded-lg border border-slate-700/80 bg-slate-800/60 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
            >
              <FileText className="h-3 w-3 text-indigo-400" />
              <span>Evaluation Reports</span>
            </Link>
            <span className="text-xs text-slate-400 font-mono">
              Status: <strong className={isApiConfigured ? 'text-emerald-400' : 'text-amber-400'}>{evalSummary?.status}</strong>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Total Evaluations */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400">Total Evaluations</p>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-white">{evalSummary?.total_evaluations ?? 0}</span>
              <span className="text-xs text-slate-500">processed</span>
            </div>
            <div className="pt-2 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-400">
              <span>Passed: <strong className="text-emerald-400">{evalSummary?.successful_evaluations ?? 0}</strong></span>
              <span>Failed: <strong className="text-rose-400">{evalSummary?.failed_evaluations ?? 0}</strong></span>
            </div>
          </div>

          {/* Average Faithfulness */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400">Avg Faithfulness</p>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-white">
                {evalSummary?.total_evaluations > 0 ? `${(evalSummary.average_faithfulness * 100).toFixed(1)}%` : 'Not Available'}
              </span>
            </div>
            <div className="pt-2 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-400">
              <span>Threshold: &ge; 70%</span>
              <span className="text-violet-400 font-mono">Grounding Ratio</span>
            </div>
          </div>

          {/* Average Answer Relevancy */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400">Avg Answer Relevancy</p>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-white">
                {evalSummary?.total_evaluations > 0 ? `${(evalSummary.average_answer_relevancy * 100).toFixed(1)}%` : 'Not Available'}
              </span>
            </div>
            <div className="pt-2 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-400">
              <span>Threshold: &ge; 70%</span>
              <span className="text-indigo-400 font-mono">Intent Match</span>
            </div>
          </div>

          {/* Hallucination Risk */}
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-2">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400">Hallucination Risk</p>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-white">
                {evalSummary?.total_evaluations > 0 ? `${(evalSummary.average_hallucination_risk * 100).toFixed(1)}%` : 'Not Available'}
              </span>
            </div>
            <div className="pt-2 border-t border-slate-800/60 flex justify-between text-[11px] text-slate-400">
              <span>Threshold: &le; 30%</span>
              <span className="text-cyan-400 font-mono">Lower is Better</span>
            </div>
          </div>
        </div>
      </section>

      {/* Navigation Tabs */}
      <div className="flex space-x-2 border-b border-slate-800">
        <button
          onClick={() => setActiveTab('individual')}
          className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'individual'
              ? 'border-violet-500 text-violet-400 bg-violet-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Play className="h-4 w-4" />
          <span>Individual Evaluation</span>
        </button>
        <button
          onClick={() => setActiveTab('benchmark')}
          className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'benchmark'
              ? 'border-violet-500 text-violet-400 bg-violet-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Benchmark Suite (28 Test Cases)</span>
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-violet-500 text-violet-400 bg-violet-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Clock className="h-4 w-4" />
          <span>Evaluation History ({history.length})</span>
        </button>
      </div>

      {/* =========================================================================
          TAB 1: Individual Evaluation
      ========================================================================= */}
      {activeTab === 'individual' && (
        <div className="space-y-6">
          {/* Sample Preset Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-400">Quick Test Cases:</span>
            {SAMPLE_BENCHMARK_PROMPTS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleFillSample(sample)}
                className="rounded-lg border border-slate-800 bg-[#0f172a] px-3 py-1.5 text-xs text-slate-300 hover:border-violet-500/40 hover:bg-violet-950/30 hover:text-white transition-all"
              >
                {sample.category}: {sample.question.slice(0, 32)}...
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Input Form Column */}
            <form onSubmit={handleRunIndividualEvaluation} className="lg:col-span-7 space-y-4 rounded-xl border border-slate-800/90 bg-[#0d1424] p-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                <h4 className="text-sm font-semibold text-white">Evaluation Parameters</h4>
                <div className="flex items-center space-x-2">
                  <label className="text-xs text-slate-400">Category:</label>
                  <select
                    value={individualForm.category}
                    onChange={(e) => setIndividualForm({ ...individualForm, category: e.target.value })}
                    className="rounded-lg border border-slate-700 bg-[#090d16] px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-violet-500"
                  >
                    <option value="Computer Science">Computer Science</option>
                    <option value="General Knowledge">General Knowledge</option>
                    <option value="Programming">Programming</option>
                    <option value="Science & Technology">Science & Technology</option>
                    <option value="Mathematics">Mathematics</option>
                    <option value="Logical Reasoning">Logical Reasoning</option>
                    <option value="Incorrect / Unsupported Claims">Incorrect / Unsupported Claims</option>
                  </select>
                </div>
              </div>

              {/* User Question */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">
                  User Question / Input Prompt <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={2}
                  value={individualForm.question}
                  onChange={(e) => setIndividualForm({ ...individualForm, question: e.target.value })}
                  placeholder="Enter the prompt or test question..."
                  className="w-full rounded-lg border border-slate-700/80 bg-[#090d16] p-3 text-xs text-slate-100 placeholder-slate-500 focus:border-violet-500 focus:outline-none"
                />
              </div>

              {/* Generated AI Response */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">
                  Generated AI Response to Evaluate <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={3}
                  value={individualForm.actual_response}
                  onChange={(e) => setIndividualForm({ ...individualForm, actual_response: e.target.value })}
                  placeholder="Enter the LLM generated answer to test..."
                  className="w-full rounded-lg border border-slate-700/80 bg-[#090d16] p-3 text-xs text-slate-100 placeholder-slate-500 focus:border-violet-500 focus:outline-none"
                />
              </div>

              {/* Reference Retrieval Context */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-slate-300">
                    Trusted Reference Context <span className="text-rose-400">*</span>
                  </label>
                  <span className="text-[11px] text-slate-500">Grounding truth for Faithfulness & Hallucination</span>
                </div>
                <textarea
                  rows={4}
                  value={individualForm.reference_context}
                  onChange={(e) => setIndividualForm({ ...individualForm, reference_context: e.target.value })}
                  placeholder="Paste ground truth context, retrieved document chunks, or factual reference data..."
                  className="w-full rounded-lg border border-slate-700/80 bg-[#090d16] p-3 text-xs text-slate-100 placeholder-slate-500 focus:border-violet-500 focus:outline-none"
                />
              </div>

              {/* Optional Expected Output */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-400">
                  Expected Output (Optional)
                </label>
                <input
                  type="text"
                  value={individualForm.expected_output}
                  onChange={(e) => setIndividualForm({ ...individualForm, expected_output: e.target.value })}
                  placeholder="Ideal gold-standard answer (optional reference)..."
                  className="w-full rounded-lg border border-slate-700/80 bg-[#090d16] px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:border-violet-500 focus:outline-none"
                />
              </div>

              {evalError && (
                <div className="rounded-lg border border-rose-900/60 bg-rose-950/40 p-3 text-xs text-rose-300 flex items-start space-x-2">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-400" />
                  <p>{evalError}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isEvaluating}
                className="w-full flex items-center justify-center space-x-2 rounded-lg bg-violet-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-violet-500 disabled:opacity-50 transition-colors shadow-md shadow-violet-950"
              >
                {isEvaluating ? (
                  <>
                    <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>DeepEval Evaluating with Gemini Judge...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5" />
                    <span>Run DeepEval Metrics</span>
                  </>
                )}
              </button>
            </form>

            {/* Results Display Column */}
            <div className="lg:col-span-5 space-y-4">
              {latestResult ? (
                <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-6 space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center space-x-2">
                      <Award className="h-4 w-4 text-violet-400" />
                      <span className="text-sm font-semibold text-white">Evaluation Scorecard</span>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${
                        latestResult.evaluation_status === 'passed'
                          ? 'bg-emerald-950/80 border border-emerald-800 text-emerald-300'
                          : latestResult.evaluation_status === 'awaiting_api_key'
                          ? 'bg-amber-950/80 border border-amber-800 text-amber-300'
                          : 'bg-rose-950/80 border border-rose-800 text-rose-300'
                      }`}
                    >
                      {latestResult.evaluation_status}
                    </span>
                  </div>

                  <div className="space-y-4">
                    {/* Faithfulness Metric Card */}
                    <div className="rounded-lg border border-slate-800 bg-[#090d16] p-4 space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-200">Faithfulness Score</span>
                        <span className="font-mono text-sm font-bold text-violet-400">
                          {latestResult.faithfulness_score !== null ? `${(latestResult.faithfulness_score * 100).toFixed(1)}%` : 'N/A'}
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-violet-500 h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min((latestResult.faithfulness_score || 0) * 100, 100)}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        {latestResult.faithfulness_reason || 'Determines whether claims in output are directly grounded in context.'}
                      </p>
                    </div>

                    {/* Answer Relevancy Metric Card */}
                    <div className="rounded-lg border border-slate-800 bg-[#090d16] p-4 space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-200">Answer Relevancy Score</span>
                        <span className="font-mono text-sm font-bold text-indigo-400">
                          {latestResult.answer_relevancy_score !== null ? `${(latestResult.answer_relevancy_score * 100).toFixed(1)}%` : 'N/A'}
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min((latestResult.answer_relevancy_score || 0) * 100, 100)}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        {latestResult.answer_relevancy_reason || 'Evaluates whether generated answer addresses user question.'}
                      </p>
                    </div>

                    {/* Hallucination / Factual Agreement Metric Card */}
                    <div className="rounded-lg border border-slate-800 bg-[#090d16] p-4 space-y-2">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-200">Factual Agreement &amp; Risk</span>
                        <div className="space-x-1.5 font-mono text-xs">
                          <span className="text-cyan-400 font-bold">
                            {latestResult.hallucination_score !== null ? `${(latestResult.hallucination_score * 100).toFixed(1)}% agreement` : 'N/A'}
                          </span>
                          <span className="text-amber-400">
                            ({latestResult.hallucination_risk !== null ? `${(latestResult.hallucination_risk * 100).toFixed(1)}% risk` : 'N/A'})
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-cyan-500 h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min((latestResult.hallucination_score || 0) * 100, 100)}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        {latestResult.hallucination_reason || 'Identifies factual contradictions or fabricated statements.'}
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/60 flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>ID: {latestResult.evaluation_id}</span>
                    <span>{new Date(latestResult.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ) : (
                <div className="h-full min-h-[300px] flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-[#0a0f1d] p-6 text-center space-y-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-800/60 text-slate-500">
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm font-medium text-slate-300">Ready for Evaluation</span>
                    <p className="text-xs text-slate-500 max-w-xs">
                      Submit a question, AI response, and grounding context to generate DeepEval metric scores.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: Benchmark Evaluation Suite
      ========================================================================= */}
      {activeTab === 'benchmark' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-6 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div className="space-y-1">
                <h4 className="text-base font-semibold text-white">LLMGuard Prepared Benchmark Suite</h4>
                <p className="text-xs text-slate-400">
                  Comprehensive 28 test-case dataset spanning Computer Science, Mathematics, Science, Logic, and Hallucination traps.
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 text-xs text-slate-400">
                  <span>Run Size:</span>
                  <select
                    value={benchmarkSampleSize}
                    onChange={(e) => setBenchmarkSampleSize(Number(e.target.value))}
                    className="rounded-lg border border-slate-700 bg-[#090d16] px-2.5 py-1 text-xs text-slate-200 focus:outline-none"
                  >
                    <option value={3}>3 Cases (Quick Test)</option>
                    <option value={5}>5 Cases (Standard)</option>
                    <option value={10}>10 Cases (Extended)</option>
                    <option value={28}>All 28 Cases (Full Benchmark)</option>
                  </select>
                </div>

                <button
                  onClick={handleRunBenchmark}
                  disabled={isBenchmarking}
                  className="flex items-center space-x-2 rounded-lg bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-500 disabled:opacity-50 transition-colors shadow-sm"
                >
                  {isBenchmarking ? (
                    <>
                      <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Running DeepEval Benchmark...</span>
                    </>
                  ) : (
                    <>
                      <Layers className="h-3.5 w-3.5" />
                      <span>Run Benchmark</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {benchmarkError && (
              <div className="rounded-lg border border-rose-900/60 bg-rose-950/40 p-3 text-xs text-rose-300">
                {benchmarkError}
              </div>
            )}

            {/* Benchmark Summary Cards */}
            {benchmarkResult && (
              <div className="space-y-5 pt-2">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 text-xs">
                    <span className="text-slate-400">Cases Evaluated</span>
                    <div className="text-lg font-bold text-white mt-1">
                      {benchmarkResult.passed_cases} / {benchmarkResult.total_cases} Passed
                    </div>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 text-xs">
                    <span className="text-slate-400">Avg Faithfulness</span>
                    <div className="text-lg font-bold text-violet-400 mt-1">
                      {(benchmarkResult.average_faithfulness * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 text-xs">
                    <span className="text-slate-400">Avg Relevancy</span>
                    <div className="text-lg font-bold text-indigo-400 mt-1">
                      {(benchmarkResult.average_answer_relevancy * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-[#090d16] p-3 text-xs">
                    <span className="text-slate-400">Hallucination Risk</span>
                    <div className="text-lg font-bold text-cyan-400 mt-1">
                      {(benchmarkResult.average_hallucination_risk * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {benchmarkResult.report_path && (
                  <div className="flex items-center justify-between rounded-lg border border-indigo-900/40 bg-indigo-950/20 px-4 py-2.5 text-xs text-indigo-300">
                    <span className="flex items-center space-x-2">
                      <FileText className="h-4 w-4" />
                      <span>Audit Report Generated: <code className="font-mono text-indigo-200">{benchmarkResult.report_path}</code></span>
                    </span>
                    <span className="text-[11px] font-mono text-emerald-400">Markdown Saved</span>
                  </div>
                )}

                {/* Per-case table */}
                <div className="overflow-x-auto rounded-lg border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#090d16] text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                      <tr>
                        <th className="p-3">ID</th>
                        <th className="p-3">Category</th>
                        <th className="p-3">Question</th>
                        <th className="p-3 text-right">Faithfulness</th>
                        <th className="p-3 text-right">Relevancy</th>
                        <th className="p-3 text-right">Agreement (Risk)</th>
                        <th className="p-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                      {benchmarkResult.results.map((r) => (
                        <tr key={r.evaluation_id} className="hover:bg-slate-800/30">
                          <td className="p-3 text-slate-400">{r.evaluation_id}</td>
                          <td className="p-3 text-slate-300 font-sans">{r.category}</td>
                          <td className="p-3 text-slate-200 font-sans max-w-xs truncate">{r.question}</td>
                          <td className="p-3 text-right text-violet-400">
                            {r.faithfulness_score !== null ? `${(r.faithfulness_score * 100).toFixed(0)}%` : 'N/A'}
                          </td>
                          <td className="p-3 text-right text-indigo-400">
                            {r.answer_relevancy_score !== null ? `${(r.answer_relevancy_score * 100).toFixed(0)}%` : 'N/A'}
                          </td>
                          <td className="p-3 text-right text-cyan-400">
                            {r.hallucination_score !== null ? `${(r.hallucination_score * 100).toFixed(0)}%` : 'N/A'}
                            <span className="text-amber-400 text-[10px] ml-1">
                              ({(r.hallucination_risk || 0 * 100).toFixed(0)}%)
                            </span>
                          </td>
                          <td className="p-3 text-center">
                            <span
                              className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase ${
                                r.evaluation_status === 'passed'
                                  ? 'bg-emerald-950/80 text-emerald-400'
                                  : 'bg-rose-950/80 text-rose-400'
                              }`}
                            >
                              {r.evaluation_status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: Evaluation History
      ========================================================================= */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800/90 bg-[#0d1424] p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h4 className="text-sm font-semibold text-white">Historical Evaluation Records</h4>
              <button
                onClick={loadSummaryAndHistory}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Refresh History</span>
              </button>
            </div>

            {history.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">
                No evaluation records saved yet. Run an individual evaluation or execute the benchmark suite to log records.
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((record) => (
                  <div
                    key={record.evaluation_id}
                    className="rounded-lg border border-slate-800 bg-[#090d16] p-4 space-y-3 transition-colors hover:border-slate-700"
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                            {record.evaluation_id}
                          </span>
                          <span className="text-xs font-semibold text-slate-300">{record.category}</span>
                        </div>
                        <h5 className="text-sm font-medium text-white">{record.question}</h5>
                      </div>
                      <span
                        className={`rounded px-2.5 py-0.5 text-[10px] font-semibold uppercase ${
                          record.evaluation_status === 'passed'
                            ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                            : record.evaluation_status === 'awaiting_api_key'
                            ? 'bg-amber-950/80 text-amber-400 border border-amber-800'
                            : 'bg-rose-950/80 text-rose-400 border border-rose-800'
                        }`}
                      >
                        {record.evaluation_status}
                      </span>
                    </div>

                    <div className="rounded bg-[#0d1424] p-3 text-xs text-slate-300 space-y-1">
                      <span className="text-[10px] uppercase font-mono text-slate-500">Evaluated Response:</span>
                      <p className="line-clamp-2">{record.actual_response}</p>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/60 text-xs font-mono">
                      <div className="flex items-center space-x-4">
                        <span>
                          Faithfulness: <strong className="text-violet-400">{record.faithfulness_score !== null ? `${(record.faithfulness_score * 100).toFixed(0)}%` : 'N/A'}</strong>
                        </span>
                        <span>
                          Relevancy: <strong className="text-indigo-400">{record.answer_relevancy_score !== null ? `${(record.answer_relevancy_score * 100).toFixed(0)}%` : 'N/A'}</strong>
                        </span>
                        <span>
                          Factual Agreement: <strong className="text-cyan-400">{record.hallucination_score !== null ? `${(record.hallucination_score * 100).toFixed(0)}%` : 'N/A'}</strong>
                        </span>
                        <span>
                          Hallucination Risk: <strong className="text-amber-400">{record.hallucination_risk !== null ? `${(record.hallucination_risk * 100).toFixed(0)}%` : 'N/A'}</strong>
                        </span>
                      </div>
                      <span className="text-slate-500 text-[11px]">{new Date(record.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
