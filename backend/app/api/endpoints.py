from typing import List, Optional
from fastapi import APIRouter, Query, status

try:
    from app.models.schemas import (
        HealthResponse,
        ProjectInfoResponse,
        ChatRequest,
        ChatResponse,
        MetricsResponse,
        EvaluationRequest,
        EvaluationResponse,
        BenchmarkRequest,
        BenchmarkSummary,
        EvaluationSummaryResponse,
        GuardrailsCheckRequest,
        GuardrailsCheckResponse,
        GuardrailsSummaryResponse,
        GuardrailsHistoryResponse,
        ObservabilitySummaryResponse,
        ObservabilityHistoryResponse,
        ObservabilityStatusResponse,
        SystemReportSummary,
        ReportExportResponse,
    )
    from app.services.system_service import SystemService
    from app.services.llm_service import llm_service
    from app.services.evaluation_service import evaluation_service
    from app.services.guardrails_service import guardrails_service
    from app.services.observability_service import observability_service
    from app.services.reports_service import reports_service
except ImportError:
    from backend.app.models.schemas import (
        HealthResponse,
        ProjectInfoResponse,
        ChatRequest,
        ChatResponse,
        MetricsResponse,
        EvaluationRequest,
        EvaluationResponse,
        BenchmarkRequest,
        BenchmarkSummary,
        EvaluationSummaryResponse,
        GuardrailsCheckRequest,
        GuardrailsCheckResponse,
        GuardrailsSummaryResponse,
        GuardrailsHistoryResponse,
        ObservabilitySummaryResponse,
        ObservabilityHistoryResponse,
        ObservabilityStatusResponse,
        SystemReportSummary,
        ReportExportResponse,
    )
    from backend.app.services.system_service import SystemService
    from backend.app.services.llm_service import llm_service
    from backend.app.services.evaluation_service import evaluation_service
    from backend.app.services.guardrails_service import guardrails_service
    from backend.app.services.observability_service import observability_service
    from backend.app.services.reports_service import reports_service

router = APIRouter()


# =========================================================================
# System Endpoints
# =========================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Backend Health Check",
    description="Returns backend status, application name, and current API version.",
    tags=["System"],
)
def get_health() -> HealthResponse:
    return SystemService.get_health()


@router.get(
    "/info",
    response_model=ProjectInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Project Overview and Roadmap",
    description="Returns basic project metadata, current development phase, and planned modules.",
    tags=["System"],
)
def get_info() -> ProjectInfoResponse:
    return SystemService.get_project_info()


# =========================================================================
# LLM Generation Endpoints (Phase 2)
# =========================================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Gemini LLM Response",
    description="Generates an AI response using Google AI Studio (Gemini API) with actual latency and token metadata.",
    tags=["LLM Playground"],
)
def chat_completion(request: ChatRequest) -> ChatResponse:
    return llm_service.generate_chat_response(
        message=request.message,
        conversation_history=request.conversation_history,
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Platform Telemetry Metrics",
    description="Returns real runtime telemetry recorded from actual Gemini API generation calls.",
    tags=["Observability"],
)
def get_metrics() -> MetricsResponse:
    return llm_service.get_metrics()


# =========================================================================
# DeepEval LLM Evaluation Endpoints (Phase 3)
# =========================================================================

@router.post(
    "/evaluation/evaluate",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate an LLM Response",
    description="Evaluates an LLM response against reference context using Faithfulness, Answer Relevancy, and Hallucination metrics.",
    tags=["LLM Evaluation"],
)
def evaluate_response(request: EvaluationRequest) -> EvaluationResponse:
    return evaluation_service.evaluate_single(
        question=request.question,
        actual_response=request.actual_response,
        reference_context=request.reference_context,
        expected_output=request.expected_output,
        category=request.category or "General",
    )


@router.post(
    "/evaluation/benchmark",
    response_model=BenchmarkSummary,
    status_code=status.HTTP_200_OK,
    summary="Run Benchmark Evaluation Suite",
    description="Runs the prepared benchmark dataset through DeepEval evaluation metrics and aggregates results.",
    tags=["LLM Evaluation"],
)
def run_benchmark(request: Optional[BenchmarkRequest] = None) -> BenchmarkSummary:
    sample_size = request.sample_size if request else None
    categories = request.categories if request else None
    return evaluation_service.run_benchmark(
        sample_size=sample_size,
        categories=categories,
    )


@router.get(
    "/evaluation/history",
    response_model=List[EvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="Evaluation History",
    description="Retrieves previous evaluation records with optional status and category filters.",
    tags=["LLM Evaluation"],
)
def get_evaluation_history(
    limit: int = Query(default=50, ge=1, le=200),
    eval_status: Optional[str] = Query(default=None, alias="status"),
    category: Optional[str] = Query(default=None),
) -> List[EvaluationResponse]:
    return evaluation_service.get_history(
        limit=limit,
        status_filter=eval_status,
        category_filter=category,
    )


@router.get(
    "/evaluation/summary",
    response_model=EvaluationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluation Aggregate Summary",
    description="Returns aggregate metric averages and operational readiness status for the evaluation dashboard.",
    tags=["LLM Evaluation"],
)
def get_evaluation_summary() -> EvaluationSummaryResponse:
    return evaluation_service.get_summary()


# =========================================================================
# Guardrails AI Safety & Moderation Endpoints (Phase 4)
# =========================================================================

@router.post(
    "/guardrails/check-input",
    response_model=GuardrailsCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate User Input Prompt",
    description="Inspects user prompts against prompt injection, jailbreak, toxicity, and integrity policies using Guardrails AI.",
    tags=["Safety Guardrails"],
)
def check_input(request: GuardrailsCheckRequest) -> GuardrailsCheckResponse:
    return guardrails_service.validate_input(text=request.text)


@router.post(
    "/guardrails/check-output",
    response_model=GuardrailsCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate LLM Generated Output",
    description="Validates AI output for toxicity, harmful content, and automatically sanitizes sensitive PII or credentials.",
    tags=["Safety Guardrails"],
)
def check_output(request: GuardrailsCheckRequest) -> GuardrailsCheckResponse:
    return guardrails_service.validate_output(text=request.text)


@router.get(
    "/guardrails/summary",
    response_model=GuardrailsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Safety Moderation Summary",
    description="Returns aggregate counts of accepted, blocked, and flagged requests from persistent SQLite safety records.",
    tags=["Safety Guardrails"],
)
def get_guardrails_summary() -> GuardrailsSummaryResponse:
    return guardrails_service.get_summary()


@router.get(
    "/guardrails/history",
    response_model=GuardrailsHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Safety Audit History",
    description="Retrieves chronological security validation logs with optional action and validation type filters.",
    tags=["Safety Guardrails"],
)
def get_guardrails_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    action: Optional[str] = Query(default=None, description="Filter by action: ALLOW, BLOCK, REDACT, FLAG"),
    validation_type: Optional[str] = Query(default=None, alias="type", description="Filter by type: input, output"),
) -> GuardrailsHistoryResponse:
    return guardrails_service.get_history(
        limit=limit,
        offset=offset,
        action_filter=action,
        type_filter=validation_type,
    )


# =========================================================================
# Observability & Tracing Endpoints (Phase 5: Langfuse)
# =========================================================================

@router.get(
    "/observability/summary",
    response_model=ObservabilitySummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Observability Summary Metrics",
    description="Returns aggregate trace counts, average latency, total token consumption, error rates, and Langfuse connection status.",
    tags=["Observability"],
)
def get_observability_summary() -> ObservabilitySummaryResponse:
    return observability_service.get_summary()


@router.get(
    "/observability/history",
    response_model=ObservabilityHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Observability Trace History",
    description="Retrieves chronological execution traces with model latency, token usage, guardrail outcomes, and status filtering.",
    tags=["Observability"],
)
def get_observability_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None, description="Filter by status: success, error, blocked, sanitized"),
) -> ObservabilityHistoryResponse:
    return observability_service.get_history(
        limit=limit,
        offset=offset,
        status_filter=status,
    )


@router.get(
    "/observability/status",
    response_model=ObservabilityStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Langfuse Connection & Telemetry Status",
    description="Returns live connection state to Langfuse Cloud, base URL, configured models, and total recorded traces.",
    tags=["Observability"],
)
def get_observability_status() -> ObservabilityStatusResponse:
    return observability_service.get_status()


# =========================================================================
# Reports & Compliance Export Endpoints (Phase 6: Integration)
# =========================================================================

@router.get(
    "/reports/summary",
    response_model=SystemReportSummary,
    status_code=status.HTTP_200_OK,
    summary="Unified System & Subsystem Report Summary",
    description="Returns cross-module platform telemetry aggregating Inference, Evaluation, Guardrails, and Observability states.",
    tags=["Reports & Compliance"],
)
def get_reports_summary() -> SystemReportSummary:
    return reports_service.get_summary()


@router.get(
    "/reports/export",
    response_model=ReportExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export Subsystem Report",
    description="Generates downloadable report content in Markdown, JSON, or CSV for system, evaluation, safety, or observability data.",
    tags=["Reports & Compliance"],
)
def export_report(
    type: str = Query(default="system", description="Report domain: 'system', 'evaluation', 'safety', 'observability'"),
    format: str = Query(default="markdown", description="Export format: 'markdown', 'json', 'csv'"),
) -> ReportExportResponse:
    return reports_service.export_report(report_type=type, export_format=format)
