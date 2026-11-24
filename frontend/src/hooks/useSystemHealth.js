import { useState, useEffect, useCallback } from 'react';
import {
  pingBackend,
  getProjectInfo,
  getMetrics,
  getEvaluationSummary,
  getGuardrailsSummary,
  getObservabilitySummary,
} from '../services/api';

export const useSystemHealth = () => {
  const [healthState, setHealthState] = useState({
    isConnected: false,
    latency: null,
    backendData: null,
    projectInfo: null,
    metrics: {
      total_requests: 0,
      average_latency_ms: 0.0,
      total_tokens: 0,
      status: 'operational',
    },
    evalSummary: {
      total_evaluations: 0,
      average_faithfulness: 0.0,
      average_answer_relevancy: 0.0,
      average_hallucination_score: 0.0,
      average_hallucination_risk: 0.0,
      successful_evaluations: 0,
      failed_evaluations: 0,
      api_configured: false,
      status: 'Awaiting Gemini API Configuration',
    },
    guardrailsSummary: {
      total_checked: 0,
      accepted_requests: 0,
      blocked_requests: 0,
      flagged_requests: 0,
      redacted_requests: 0,
      injection_detections: 0,
      toxicity_detections: 0,
      unsafe_output_detections: 0,
      jailbreak_detections: 0,
      sensitive_data_detections: 0,
      status: 'operational',
    },
    observabilitySummary: {
      total_traces: 0,
      successful_requests: 0,
      failed_requests: 0,
      average_latency_ms: 0.0,
      total_input_tokens: 0,
      total_output_tokens: 0,
      total_tokens_consumed: 0,
      connection_status: 'Not Configured',
      is_configured: false,
    },
    loading: true,
    error: null,
    lastChecked: null,
  });

  const checkConnectivity = useCallback(async () => {
    setHealthState((prev) => ({ ...prev, loading: true, error: null }));
    const pingResult = await pingBackend();

    if (pingResult.connected) {
      try {
        const [info, metrics, evalSummary, guardrailsSummary, obsSummary] = await Promise.all([
          getProjectInfo().catch(() => null),
          getMetrics().catch(() => ({
            total_requests: 0,
            average_latency_ms: 0.0,
            total_tokens: 0,
            status: 'operational',
          })),
          getEvaluationSummary().catch(() => ({
            total_evaluations: 0,
            average_faithfulness: 0.0,
            average_answer_relevancy: 0.0,
            average_hallucination_score: 0.0,
            average_hallucination_risk: 0.0,
            successful_evaluations: 0,
            failed_evaluations: 0,
            api_configured: false,
            status: 'Awaiting Gemini API Configuration',
          })),
          getGuardrailsSummary().catch(() => ({
            total_checked: 0,
            accepted_requests: 0,
            blocked_requests: 0,
            flagged_requests: 0,
            redacted_requests: 0,
            injection_detections: 0,
            toxicity_detections: 0,
            unsafe_output_detections: 0,
            jailbreak_detections: 0,
            sensitive_data_detections: 0,
            status: 'operational',
          })),
          getObservabilitySummary().catch(() => ({
            total_traces: 0,
            successful_requests: 0,
            failed_requests: 0,
            average_latency_ms: 0.0,
            total_input_tokens: 0,
            total_output_tokens: 0,
            total_tokens_consumed: 0,
            connection_status: 'Not Configured',
            is_configured: false,
          })),
        ]);

        setHealthState({
          isConnected: true,
          latency: pingResult.latencyMs,
          backendData: pingResult.data,
          projectInfo: info,
          metrics: metrics || {
            total_requests: 0,
            average_latency_ms: 0.0,
            total_tokens: 0,
            status: 'operational',
          },
          evalSummary: evalSummary || {
            total_evaluations: 0,
            average_faithfulness: 0.0,
            average_answer_relevancy: 0.0,
            average_hallucination_score: 0.0,
            average_hallucination_risk: 0.0,
            successful_evaluations: 0,
            failed_evaluations: 0,
            api_configured: false,
            status: 'Awaiting Gemini API Configuration',
          },
          guardrailsSummary: guardrailsSummary || {
            total_checked: 0,
            accepted_requests: 0,
            blocked_requests: 0,
            flagged_requests: 0,
            redacted_requests: 0,
            injection_detections: 0,
            toxicity_detections: 0,
            unsafe_output_detections: 0,
            jailbreak_detections: 0,
            sensitive_data_detections: 0,
            status: 'operational',
          },
          observabilitySummary: obsSummary || {
            total_traces: 0,
            successful_requests: 0,
            failed_requests: 0,
            average_latency_ms: 0.0,
            total_input_tokens: 0,
            total_output_tokens: 0,
            total_tokens_consumed: 0,
            connection_status: 'Not Configured',
            is_configured: false,
          },
          loading: false,
          error: null,
          lastChecked: new Date().toLocaleTimeString(),
        });
      } catch (err) {
        setHealthState({
          isConnected: true,
          latency: pingResult.latencyMs,
          backendData: pingResult.data,
          projectInfo: null,
          metrics: {
            total_requests: 0,
            average_latency_ms: 0.0,
            total_tokens: 0,
            status: 'operational',
          },
          evalSummary: {
            total_evaluations: 0,
            average_faithfulness: 0.0,
            average_answer_relevancy: 0.0,
            average_hallucination_score: 0.0,
            average_hallucination_risk: 0.0,
            successful_evaluations: 0,
            failed_evaluations: 0,
            api_configured: false,
            status: 'Awaiting Gemini API Configuration',
          },
          guardrailsSummary: {
            total_checked: 0,
            accepted_requests: 0,
            blocked_requests: 0,
            flagged_requests: 0,
            redacted_requests: 0,
            injection_detections: 0,
            toxicity_detections: 0,
            unsafe_output_detections: 0,
            jailbreak_detections: 0,
            sensitive_data_detections: 0,
            status: 'operational',
          },
          loading: false,
          error: 'Health endpoint reachable, but metadata endpoints returned an error.',
          lastChecked: new Date().toLocaleTimeString(),
        });
      }
    } else {
      setHealthState((prev) => ({
        ...prev,
        isConnected: false,
        latency: null,
        backendData: null,
        projectInfo: null,
        loading: false,
        error: pingResult.error,
        lastChecked: new Date().toLocaleTimeString(),
      }));
    }
  }, []);

  useEffect(() => {
    checkConnectivity();

    // Auto-check connectivity every 20 seconds
    const interval = setInterval(checkConnectivity, 20000);
    return () => clearInterval(interval);
  }, [checkConnectivity]);

  return {
    ...healthState,
    refresh: checkConnectivity,
  };
};
