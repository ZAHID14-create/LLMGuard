from typing import List, Optional, Union
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Current backend status (e.g., healthy)")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current ISO 8601 UTC timestamp")
    environment: str = Field(..., description="Current execution environment")


class PlannedModule(BaseModel):
    name: str = Field(..., description="Module name")
    key: str = Field(..., description="Module identifier key")
    description: str = Field(..., description="Description of module responsibilities")
    tool: str = Field(..., description="Target open-source framework or API")
    phase: int = Field(..., description="Project phase when this module is implemented")
    status: str = Field(..., description="Status label")


class ProjectInfoResponse(BaseModel):
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    version: str = Field(..., description="Project version")
    current_phase: str = Field(..., description="Currently active development phase")
    framework: str = Field(..., description="Backend and frontend framework details")
    planned_modules: List[PlannedModule] = Field(..., description="List of planned core modules")
    gemini_model: Optional[str] = Field(default=None, description="Active Gemini LLM model identifier")
    documentation_url: Optional[str] = Field(default="/docs", description="Interactive OpenAPI documentation URL")


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message author role: 'user' or 'model' / 'assistant'")
    content: str = Field(..., description="Text content of the message")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Prompt message to send to Gemini LLM")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Prior conversation history turns for contextual dialogue"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Generated text response from Gemini LLM")
    model: str = Field(..., description="Name of the Gemini model used for generation")
    prompt_tokens: Optional[int] = Field(default=None, description="Actual input prompt tokens consumed")
    completion_tokens: Optional[int] = Field(default=None, description="Actual output candidate tokens consumed")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens consumed")
    latency_ms: float = Field(..., description="Roundtrip execution latency in milliseconds")
    status: str = Field(default="success", description="Status code or indicator")
    guardrails_result: Optional[dict] = Field(default=None, description="Guardrails safety validation metadata")
    trace_id: Optional[str] = Field(default=None, description="Langfuse observability trace identifier")
    is_simulated: bool = Field(default=False, description="Whether this response was generated in Simulation Mode without live Gemini API credentials")


class MetricsResponse(BaseModel):
    total_requests: int = Field(..., description="Total live LLM generation requests processed")
    simulated_requests: int = Field(default=0, description="Total generation requests processed in Simulation Mode")
    average_latency_ms: float = Field(..., description="Average roundtrip response latency in milliseconds")
    total_tokens: int = Field(..., description="Total actual tokens consumed across all live requests")
    status: str = Field(default="operational", description="Metrics service status")


# =========================================================================
# Phase 3 – DeepEval LLM Evaluation Schemas
# =========================================================================

class EvaluationRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Original user prompt or test question")
    actual_response: str = Field(..., min_length=1, description="LLM generated answer to evaluate")
    reference_context: Union[str, List[str]] = Field(
        ...,
        description="Trusted grounding or retrieval context required for Faithfulness and Hallucination checks"
    )
    expected_output: Optional[str] = Field(
        default=None,
        description="Optional ground truth reference answer"
    )
    category: Optional[str] = Field(
        default="General",
        description="Evaluation category tag"
    )


class EvaluationResponse(BaseModel):
    evaluation_id: str = Field(..., description="Unique evaluation record ID")
    timestamp: str = Field(..., description="Execution timestamp (ISO UTC)")
    question: str = Field(..., description="Evaluated question")
    actual_response: str = Field(..., description="Evaluated LLM response")
    reference_context: List[str] = Field(..., description="Reference contexts used during evaluation")
    expected_output: Optional[str] = Field(default=None, description="Optional ground truth")
    faithfulness_score: Optional[float] = Field(default=None, description="Faithfulness score (0.0 to 1.0)")
    faithfulness_reason: Optional[str] = Field(default=None, description="Reasoning for faithfulness score")
    answer_relevancy_score: Optional[float] = Field(default=None, description="Answer Relevancy score (0.0 to 1.0)")
    answer_relevancy_reason: Optional[str] = Field(default=None, description="Reasoning for relevancy score")
    hallucination_score: Optional[float] = Field(
        default=None,
        description="Raw DeepEval HallucinationMetric factual agreement score (1.0 = completely faithful, 0.0 = completely hallucinated)"
    )
    hallucination_risk: Optional[float] = Field(
        default=None,
        description="Calculated Hallucination Risk (1.0 - raw score; 0.0 = no risk, 1.0 = high risk)"
    )
    hallucination_reason: Optional[str] = Field(default=None, description="Reasoning for hallucination score")
    evaluation_status: str = Field(..., description="'passed', 'failed', 'awaiting_api_key', or 'error'")
    category: Optional[str] = Field(default="General", description="Category tag")
    error: Optional[str] = Field(default=None, description="Error message if evaluation failed")


class BenchmarkRequest(BaseModel):
    sample_size: Optional[int] = Field(
        default=None,
        description="Number of benchmark test cases to evaluate (default: all available)"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Optional list of categories to filter by"
    )


class BenchmarkSummary(BaseModel):
    benchmark_id: str = Field(..., description="Unique benchmark execution run ID")
    timestamp: str = Field(..., description="Benchmark execution timestamp (ISO UTC)")
    total_cases: int = Field(..., description="Total benchmark test cases processed")
    passed_cases: int = Field(..., description="Count of cases meeting all thresholds")
    failed_cases: int = Field(..., description="Count of cases failing one or more thresholds")
    average_faithfulness: float = Field(..., description="Mean faithfulness score across cases")
    average_answer_relevancy: float = Field(..., description="Mean answer relevancy score across cases")
    average_hallucination_score: float = Field(..., description="Mean factual agreement score")
    average_hallucination_risk: float = Field(..., description="Mean hallucination risk (1 - agreement)")
    results: List[EvaluationResponse] = Field(..., description="Detailed per-test results")
    report_path: Optional[str] = Field(default=None, description="File path of saved markdown audit report")
    status: str = Field(default="completed", description="Benchmark status")


class EvaluationSummaryResponse(BaseModel):
    total_evaluations: int = Field(..., description="Total individual and benchmark evaluations recorded")
    average_faithfulness: float = Field(..., description="Overall average faithfulness score")
    average_answer_relevancy: float = Field(..., description="Overall average answer relevancy score")
    average_hallucination_score: float = Field(..., description="Overall average factual agreement score")
    average_hallucination_risk: float = Field(..., description="Overall average hallucination risk")
    successful_evaluations: int = Field(..., description="Count of passed evaluations")
    failed_evaluations: int = Field(..., description="Count of failed evaluations")
    api_configured: bool = Field(..., description="Whether Gemini API is configured for live evaluation")
    status: str = Field(..., description="Status message (e.g. 'Operational' or 'Awaiting Gemini API Configuration')")


# =========================================================================
# Phase 4 – Guardrails AI Safety & Moderation Schemas
# =========================================================================

class GuardrailsCheckRequest(BaseModel):
    text: str = Field(..., description="Prompt or response text to validate with Guardrails AI")


class GuardrailsCheckResponse(BaseModel):
    validation_status: str = Field(..., description="Overall validation status: 'passed' or 'failed'")
    action: str = Field(..., description="Enforced action: 'ALLOW', 'BLOCK', 'REDACT', or 'FLAG'")
    risk_category: str = Field(..., description="Identified threat or risk category")
    severity: str = Field(..., description="Severity classification: 'None', 'Low', 'Medium', 'High', or 'Critical'")
    reason: str = Field(..., description="Human-readable justification for the safety decision")
    detected_issues: List[str] = Field(default_factory=list, description="Specific triggers or patterns detected")
    sanitized_text: Optional[str] = Field(default=None, description="Redacted or cleaned text where applicable")
    record_id: Optional[str] = Field(default=None, description="Persistent safety log record ID")
    timestamp: Optional[str] = Field(default=None, description="Validation timestamp (ISO UTC)")


class GuardrailsSummaryResponse(BaseModel):
    total_checked: int = Field(..., description="Total input and output checks executed")
    accepted_requests: int = Field(..., description="Total requests passed and allowed")
    blocked_requests: int = Field(..., description="Total requests blocked due to security/policy violations")
    flagged_requests: int = Field(..., description="Total requests flagged for auditing")
    redacted_requests: int = Field(..., description="Total responses with sensitive information redacted")
    injection_detections: int = Field(..., description="Count of prompt injection attempts detected")
    toxicity_detections: int = Field(..., description="Count of toxic/abusive inputs or outputs detected")
    unsafe_output_detections: int = Field(..., description="Count of unsafe or policy-violating outputs detected")
    jailbreak_detections: int = Field(default=0, description="Count of jailbreak attempts detected")
    sensitive_data_detections: int = Field(default=0, description="Count of sensitive PII or secret exposure detections")
    status: str = Field(default="operational", description="Safety moderation service status")


class GuardrailsLogItem(BaseModel):
    id: str = Field(..., description="Log record identifier")
    timestamp: str = Field(..., description="UTC ISO timestamp")
    validation_type: str = Field(..., description="Validation point: 'input', 'output', or 'chat_pipeline'")
    risk_category: str = Field(..., description="Risk category detected")
    severity: str = Field(..., description="Risk severity")
    action: str = Field(..., description="Action taken: ALLOW, BLOCK, REDACT, FLAG")
    validation_reason: str = Field(..., description="Reason for validation result")
    detected_issues: List[str] = Field(default_factory=list, description="List of matched patterns or issues")
    input_snippet: str = Field(..., description="Safe, truncated representation of inspected text")
    status: str = Field(..., description="Status: passed, blocked, flagged, redacted")


class GuardrailsHistoryResponse(BaseModel):
    total: int = Field(..., description="Total number of historical safety logs")
    logs: List[GuardrailsLogItem] = Field(..., description="Chronological list of safety validation logs")


# =========================================================================
# Phase 5 – Langfuse LLM Observability Schemas
# =========================================================================

class TraceItem(BaseModel):
    trace_id: str = Field(..., description="Unique observability trace ID")
    timestamp: str = Field(..., description="Execution timestamp (ISO UTC)")
    name: str = Field(..., description="Observation span or trace name")
    model: Optional[str] = Field(default=None, description="Model identifier used")
    latency_ms: float = Field(..., description="Roundtrip execution latency in milliseconds")
    prompt_tokens: Optional[int] = Field(default=None, description="Actual input prompt tokens")
    completion_tokens: Optional[int] = Field(default=None, description="Actual output completion tokens")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens consumed")
    status: str = Field(..., description="Execution status: 'success', 'blocked', 'error', 'sanitized'")
    error_type: Optional[str] = Field(default=None, description="Exception or error type when failed")
    error_message: Optional[str] = Field(default=None, description="Error description or reason")
    guardrail_status: Optional[str] = Field(default=None, description="Safety action: ALLOW, BLOCK, REDACT")
    risk_category: Optional[str] = Field(default=None, description="Safety threat category if intercepted")
    eval_metric: Optional[str] = Field(default=None, description="Associated DeepEval metric evaluated")
    eval_score: Optional[float] = Field(default=None, description="DeepEval evaluation score")
    is_remote: bool = Field(default=False, description="Whether trace was synced to Langfuse Cloud")


class ObservabilitySummaryResponse(BaseModel):
    total_traces: int = Field(..., description="Total captured request and observation traces")
    successful_requests: int = Field(..., description="Total successful executions")
    failed_requests: int = Field(..., description="Total failed or errored requests")
    average_latency_ms: float = Field(..., description="Average response latency across recorded traces")
    total_input_tokens: int = Field(..., description="Total input tokens consumed")
    total_output_tokens: int = Field(..., description="Total output completion tokens consumed")
    total_tokens_consumed: int = Field(..., description="Combined total token consumption")
    connection_status: str = Field(..., description="Langfuse Cloud connection status ('Connected', 'Not Configured', 'Connection Error')")
    is_configured: bool = Field(..., description="Whether valid Langfuse keys are configured")
    total_llm_requests: int = Field(default=0, description="Total LLM requests (successful + failed, excluding evaluations)")
    simulated_requests: int = Field(default=0, description="Total simulated requests")
    cloud_synced_traces: int = Field(default=0, description="Total traces synced to Langfuse Cloud")
    local_only_traces: int = Field(default=0, description="Total traces stored only in local SQLite")


class ObservabilityHistoryResponse(BaseModel):
    total: int = Field(..., description="Total recorded trace count")
    traces: List[TraceItem] = Field(..., description="Chronological trace records")


class ObservabilityStatusResponse(BaseModel):
    is_configured: bool = Field(..., description="Whether Langfuse credentials are provided")
    sdk_initialized: bool = Field(..., description="Whether official Langfuse Python SDK initialized")
    connection_status: str = Field(..., description="Current status: Connected, Not Configured, Connection Error")
    base_url: str = Field(..., description="Configured Langfuse host URL")
    last_trace_timestamp: Optional[str] = Field(default=None, description="Timestamp of the most recent recorded trace")
    guidance: str = Field(..., description="Setup instructions or connection diagnostic details")


# =========================================================================
# Phase 6 – Integrated Reporting Schemas
# =========================================================================

class SystemReportSummary(BaseModel):
    generated_at: str = Field(..., description="Report generation timestamp in ISO UTC")
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Platform version")
    environment: str = Field(..., description="Environment")
    current_phase: str = Field(..., description="Current milestone phase")
    llm_metrics: MetricsResponse = Field(..., description="Gemini inference statistics")
    evaluation_summary: EvaluationSummaryResponse = Field(..., description="DeepEval evaluation summary")
    guardrails_summary: GuardrailsSummaryResponse = Field(..., description="Guardrails AI safety summary")
    observability_summary: ObservabilitySummaryResponse = Field(..., description="Langfuse observability summary")


class ReportExportResponse(BaseModel):
    report_type: str = Field(..., description="Type of report: 'system', 'evaluation', 'safety', 'observability'")
    format: str = Field(..., description="Export format: 'json', 'markdown', 'csv'")
    filename: str = Field(..., description="Suggested filename for download")
    generated_at: str = Field(..., description="Timestamp of generation")
    content: str = Field(..., description="Formatted string content of the exported report")
