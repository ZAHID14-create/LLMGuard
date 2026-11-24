import axios from 'axios';

/**
 * Base URL for the FastAPI backend API.
 * Configured via frontend/.env (VITE_API_BASE_URL) with localhost:8000 fallback.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Axios instance with timeout and JSON headers
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60s timeout for DeepEval batch and LLM judge calls
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorDetails = {
      message:
        error.response?.data?.detail ||
        error.message ||
        'Network error occurred communicating with LLMGuard backend',
      status: error.response?.status || null,
      data: error.response?.data || null,
      isNetworkError: !error.response,
    };
    return Promise.reject(errorDetails);
  }
);

// =========================================================================
// System & Telemetry Endpoints
// =========================================================================

export const getHealth = async () => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

export const getProjectInfo = async () => {
  const response = await apiClient.get('/api/info');
  return response.data;
};

export const getMetrics = async () => {
  const response = await apiClient.get('/api/metrics');
  return response.data;
};

// =========================================================================
// LLM Chat Playground Service
// =========================================================================

export const sendChatMessage = async ({ message, conversation_history = [] }) => {
  const response = await apiClient.post('/api/chat', {
    message,
    conversation_history,
  });
  return response.data;
};

// =========================================================================
// DeepEval LLM Evaluation Endpoints
// =========================================================================

export const evaluateResponse = async ({
  question,
  actual_response,
  reference_context,
  expected_output = null,
  category = 'General',
}) => {
  const response = await apiClient.post('/api/evaluation/evaluate', {
    question,
    actual_response,
    reference_context,
    expected_output,
    category,
  });
  return response.data;
};

export const runBenchmark = async ({ sample_size = null, categories = null } = {}) => {
  const response = await apiClient.post('/api/evaluation/benchmark', {
    sample_size,
    categories,
  });
  return response.data;
};

export const getEvaluationHistory = async ({ limit = 50, status = null, category = null } = {}) => {
  const params = { limit };
  if (status) params.status = status;
  if (category) params.category = category;

  const response = await apiClient.get('/api/evaluation/history', { params });
  return response.data;
};

export const getEvaluationSummary = async () => {
  const response = await apiClient.get('/api/evaluation/summary');
  return response.data;
};

// =========================================================================
// Guardrails AI Safety & Moderation Endpoints
// =========================================================================

export const checkInput = async (text) => {
  const response = await apiClient.post('/api/guardrails/check-input', { text });
  return response.data;
};

export const checkOutput = async (text) => {
  const response = await apiClient.post('/api/guardrails/check-output', { text });
  return response.data;
};

export const getGuardrailsSummary = async () => {
  const response = await apiClient.get('/api/guardrails/summary');
  return response.data;
};

export const getGuardrailsHistory = async ({ limit = 50, offset = 0, action = null, type = null } = {}) => {
  const params = { limit, offset };
  if (action) params.action = action;
  if (type) params.type = type;
  const response = await apiClient.get('/api/guardrails/history', { params });
  return response.data;
};

// =========================================================================
// Langfuse LLM Observability Endpoints
// =========================================================================

export const getObservabilitySummary = async () => {
  const response = await apiClient.get('/api/observability/summary');
  return response.data;
};

export const getObservabilityHistory = async ({ limit = 50, offset = 0, status = null } = {}) => {
  const params = { limit, offset };
  if (status) params.status = status;
  const response = await apiClient.get('/api/observability/history', { params });
  return response.data;
};

export const getObservabilityStatus = async () => {
  const response = await apiClient.get('/api/observability/status');
  return response.data;
};

// =========================================================================
// Reports & Export Endpoints
// =========================================================================

export const getReportsSummary = async () => {
  const response = await apiClient.get('/api/reports/summary');
  return response.data;
};

export const exportReport = async ({ type = 'system', format = 'markdown' } = {}) => {
  const params = { type, format };
  const response = await apiClient.get('/api/reports/export', { params });
  return response.data;
};

/**
 * Ping backend to measure roundtrip latency and connectivity
 */
export const pingBackend = async () => {
  const startTime = performance.now();
  try {
    const health = await getHealth();
    const endTime = performance.now();
    return {
      connected: true,
      latencyMs: Math.round(endTime - startTime),
      data: health,
      error: null,
    };
  } catch (err) {
    return {
      connected: false,
      latencyMs: null,
      data: null,
      error: err.message || 'Unable to connect to backend server',
    };
  }
};

export default apiClient;
