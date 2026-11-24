import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Send,
  Trash2,
  Bot,
  User,
  Sparkles,
  Clock,
  Zap,
  AlertCircle,
  Copy,
  Check,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Activity,
  ExternalLink,
} from 'lucide-react';
import { sendChatMessage, getProjectInfo } from '../services/api';

const STARTER_PROMPTS = [
  'Explain the difference between LLM hallucination and answer relevance.',
  'What are common prompt injection attack vectors and how do guardrails prevent them?',
  'Generate a JSON test scenario for an enterprise customer service chatbot.',
  'How does Time-to-First-Token (TTFT) impact user experience in conversational AI?',
];

export const Playground = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorBanner, setErrorBanner] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [activeModel, setActiveModel] = useState('gemini-3.5-flash-lite');

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    getProjectInfo()
      .then((info) => {
        if (info?.gemini_model) setActiveModel(info.gemini_model);
      })
      .catch(() => {});
  }, []);

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Adjust textarea height automatically
  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  const handleSendMessage = async (customPrompt) => {
    const textToSend = typeof customPrompt === 'string' ? customPrompt : inputMessage;
    if (!textToSend.trim() || isLoading) return;

    setErrorBanner(null);
    const userTurn = {
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    // Prepare conversation history to send (previous turns only)
    const historyPayload = messages.map((m) => ({
      role: m.role === 'model' ? 'model' : 'user',
      content: m.content,
    }));

    setMessages((prev) => [...prev, userTurn]);
    setInputMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsLoading(true);

    try {
      const responseData = await sendChatMessage({
        message: textToSend.trim(),
        conversation_history: historyPayload,
      });

      const modelTurn = {
        role: 'model',
        content: responseData.response,
        model: responseData.model,
        prompt_tokens: responseData.prompt_tokens,
        completion_tokens: responseData.completion_tokens,
        total_tokens: responseData.total_tokens,
        latency_ms: responseData.latency_ms,
        status: responseData.status,
        guardrails_result: responseData.guardrails_result,
        trace_id: responseData.trace_id,
        is_simulated: Boolean(responseData.is_simulated),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      if (responseData.model && !responseData.is_simulated) {
        setActiveModel(responseData.model);
      }
      setMessages((prev) => [...prev, modelTurn]);
    } catch (err) {
      console.error('Chat generation error:', err);
      let errorMsg = err.message || 'Failed to generate response from Gemini API.';

      if (err.status === 500 && (errorMsg.includes('GEMINI_API_KEY') || errorMsg.includes('not configured'))) {
        errorMsg = 'AI service is temporarily unavailable. Please try again later.';
      } else if (err.status === 401) {
        errorMsg = 'AI service is temporarily unavailable. Please try again later.';
      } else if (err.status === 429) {
        errorMsg = 'AI service rate limit exceeded. Please wait a moment before sending another message.';
      } else if (err.message?.includes('Network Error')) {
        errorMsg = 'Unable to connect to AI service. Please verify server connection.';
      }

      setErrorBanner(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setErrorBanner(null);
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-8.5rem)] max-w-6xl flex-col rounded-2xl border border-slate-800/90 bg-[#0c1220] shadow-xl overflow-hidden">
      {/* Playground Header Bar */}
      <div className="flex h-14 items-center justify-between border-b border-slate-800/90 bg-[#0d1424] px-5">
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-950/80 border border-indigo-700/60 text-indigo-400">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold text-white">Gemini AI Playground</span>
              <span className="rounded bg-indigo-950/80 border border-indigo-800/80 px-2 py-0.5 text-[10px] font-mono text-indigo-300">
                {activeModel}
              </span>
            </div>
            <span className="text-[11px] text-slate-400 hidden sm:inline">
              Multi-turn conversational inference via Google AI Studio GenAI SDK
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="flex items-center space-x-1.5 rounded-lg border border-slate-700/80 bg-slate-800/60 px-2.5 py-1 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
              title="Clear current session dialogue"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear Session</span>
            </button>
          )}
          <span className="rounded-full bg-slate-800/80 px-2.5 py-1 text-[11px] font-mono text-slate-400">
            {messages.length} {messages.length === 1 ? 'turn' : 'turns'}
          </span>
        </div>
      </div>

      {/* Error Notification Banner */}
      {errorBanner && (
        <div className="flex items-start justify-between border-b border-rose-900/60 bg-rose-950/50 p-3.5 text-xs text-rose-300">
          <div className="flex items-start space-x-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold text-rose-200">Execution Error</span>
              <p className="text-rose-300/90 leading-relaxed">{errorBanner}</p>
            </div>
          </div>
          <button
            onClick={() => setErrorBanner(null)}
            className="text-rose-400 hover:text-rose-200 text-xs ml-3"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Message List Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center space-y-4 max-w-lg mx-auto py-8">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-950/40 border border-indigo-800/50 text-indigo-400 shadow-inner">
              <Sparkles className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white tracking-tight">
                LLMGuard AI Playground
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Send prompts to Google Gemini to inspect real-time responses, actual token consumption, and generation latency.
              </p>
            </div>

            {/* Quick Starter Chips */}
            <div className="w-full space-y-2 pt-2">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Suggested Prompts
              </div>
              <div className="grid grid-cols-1 gap-2 text-left">
                {STARTER_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(prompt)}
                    className="rounded-lg border border-slate-800 bg-[#0f172a] p-2.5 text-xs text-slate-300 hover:border-indigo-500/40 hover:bg-indigo-950/20 hover:text-white transition-all text-left"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={index}
                className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${
                    isUser
                      ? 'bg-blue-600 text-white'
                      : 'bg-gradient-to-br from-indigo-600 to-violet-600 text-white shadow-sm shadow-indigo-950'
                  }`}
                >
                  {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>

                {/* Bubble Container */}
                <div className={`max-w-[80%] space-y-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'border border-slate-800/90 bg-[#101728] text-slate-100 rounded-tl-none'
                    }`}
                  >
                    <div className="whitespace-pre-wrap break-words">{msg.content}</div>

                    {!isUser && (
                      <div className="mt-2.5 flex items-center justify-end pt-1 border-t border-slate-800/60">
                        <button
                          onClick={() => handleCopy(msg.content, index)}
                          className="flex items-center space-x-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
                          title="Copy response text"
                        >
                          {copiedIndex === index ? (
                            <>
                              <Check className="h-3 w-3 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Non-fabricated Gemini Metadata Footer */}
                  {!isUser && (
                    <div className="flex flex-wrap items-center gap-1.5 px-1 text-[10px] font-mono text-slate-400">
                      {msg.status === 'blocked' ? (
                        <span className="inline-flex items-center space-x-1 rounded bg-rose-950/80 border border-rose-800/80 px-2 py-0.5 text-rose-300 font-semibold font-sans">
                          <ShieldAlert className="h-3 w-3 text-rose-400" />
                          <span>Input Blocked by Guardrails AI ({msg.guardrails_result?.risk_category || 'Policy Violation'})</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 rounded bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 text-emerald-400 font-sans">
                          <ShieldCheck className="h-3 w-3" />
                          <span>Input Verified</span>
                        </span>
                      )}

                      {msg.status === 'sanitized' && (
                        <span className="inline-flex items-center space-x-1 rounded bg-cyan-950/80 border border-cyan-800/80 px-2 py-0.5 text-cyan-300 font-semibold font-sans">
                          <ShieldAlert className="h-3 w-3 text-cyan-400" />
                          <span>Output Sanitized (PII/Secret Redacted)</span>
                        </span>
                      )}

                      {msg.status === 'success' && (
                        <span className="inline-flex items-center space-x-1 rounded bg-indigo-950/80 border border-indigo-800/80 px-2 py-0.5 text-indigo-300 font-sans">
                          <Bot className="h-3 w-3 text-indigo-400" />
                          <span>Response Generated</span>
                        </span>
                      )}

                      {(msg.is_simulated || msg.status === 'simulated') && (
                        <span className="inline-flex items-center space-x-1 rounded bg-amber-950/80 border border-amber-800/80 px-2 py-0.5 text-amber-300 font-sans font-semibold">
                          <AlertCircle className="h-3 w-3 text-amber-400" />
                          <span>Simulated Response</span>
                        </span>
                      )}

                      <span className="rounded bg-slate-800/80 px-2 py-0.5 text-slate-300">
                        {msg.model || 'gemini-3.5-flash-lite'}
                      </span>

                      {msg.latency_ms !== undefined && msg.latency_ms !== null && (
                        <span className="flex items-center space-x-1 rounded bg-slate-800/80 px-2 py-0.5 text-amber-300">
                          <Clock className="h-2.5 w-2.5" />
                          <span>{msg.latency_ms} ms</span>
                        </span>
                      )}

                      {msg.is_simulated ? (
                        <span className="flex items-center space-x-1 rounded bg-slate-800/80 px-2 py-0.5 text-slate-400" title="Token counts are unavailable for simulated responses">
                          <Zap className="h-2.5 w-2.5 text-amber-400" />
                          <span>Tokens: N/A</span>
                        </span>
                      ) : (
                        msg.total_tokens !== undefined && msg.total_tokens !== null && (
                          <span className="flex items-center space-x-1 rounded bg-slate-800/80 px-2 py-0.5 text-cyan-300">
                            <Zap className="h-2.5 w-2.5" />
                            <span>
                              Tokens: {msg.prompt_tokens ?? 0} in / {msg.completion_tokens ?? 0} out ({msg.total_tokens} total)
                            </span>
                          </span>
                        )
                      )}

                      {msg.trace_id && (
                        <Link
                          to="/observability"
                          title="Inspect trace in Observability module"
                          className="inline-flex items-center space-x-1 rounded bg-indigo-950/90 border border-indigo-800/90 px-2 py-0.5 text-indigo-300 hover:bg-indigo-900/90 transition-colors"
                        >
                          <Activity className="h-2.5 w-2.5 text-indigo-400" />
                          <span>Trace #{msg.trace_id.substring(0, 10)}...</span>
                          <ExternalLink className="h-2 w-2 opacity-70" />
                        </Link>
                      )}

                      <span className="text-slate-500">{msg.timestamp}</span>
                    </div>
                  )}

                  {isUser && (
                    <div className="text-right text-[10px] font-mono text-slate-500 px-1">
                      {msg.timestamp}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {/* Loading / Typing Indicator */}
        {isLoading && (
          <div className="flex items-start space-x-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 text-white">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-none border border-slate-800/90 bg-[#101728] px-4 py-3 shadow-sm">
              <div className="flex items-center space-x-2 text-xs text-slate-400">
                <span className="font-medium text-indigo-400">Gemini is thinking</span>
                <span className="flex space-x-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.3s]"></span>
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.15s]"></span>
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400"></span>
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Bar */}
      <div className="border-t border-slate-800/90 bg-[#0d1424] p-4">
        <div className="relative flex items-end rounded-xl border border-slate-700/80 bg-[#090d16] p-2 focus-within:border-indigo-500/80 focus-within:ring-1 focus-within:ring-indigo-500/30 transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputMessage}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Type your prompt here... (Press Enter to send, Shift+Enter for newline)"
            className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-30 disabled:hover:bg-indigo-600 transition-colors shadow-sm shadow-indigo-950"
            title="Send prompt to Gemini"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 px-1">
          <span>
            Provider: <strong className="text-slate-400">Google AI Studio</strong> (Gemini API)
          </span>
          <span>Shift + Enter for new lines</span>
        </div>
      </div>
    </div>
  );
};
