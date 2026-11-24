from datetime import datetime, timezone

try:
    from app.core.config import settings
    from app.models.schemas import HealthResponse, ProjectInfoResponse, PlannedModule
except ImportError:
    from backend.app.core.config import settings
    from backend.app.models.schemas import HealthResponse, ProjectInfoResponse, PlannedModule


class SystemService:
    """Service providing core system health and architectural metadata."""

    @staticmethod
    def get_health() -> HealthResponse:
        """Construct the system health status response."""
        return HealthResponse(
            status="healthy",
            app_name=settings.PROJECT_NAME,
            version=settings.API_VERSION,
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment=settings.ENVIRONMENT,
        )

    @staticmethod
    def get_project_info() -> ProjectInfoResponse:
        """Construct project overview information with roadmap modules."""
        modules = [
            PlannedModule(
                name="LLM Generation Engine",
                key="gemini_llm",
                description="Ultra-fast LLM response generation using Google AI Studio (Gemini API, Flash models).",
                tool="Google Gemini API",
                phase=2,
                status="Integrated & Operational",
            ),
            PlannedModule(
                name="LLM Evaluation Engine",
                key="deepeval",
                description="Automated unit testing for LLMs evaluating Faithfulness, Answer Relevancy, and Hallucination.",
                tool="DeepEval",
                phase=3,
                status="Integrated & Operational",
            ),
            PlannedModule(
                name="Safety Guardrails",
                key="guardrails_ai",
                description="Real-time input/output validation, PII anonymization, prompt injection defense, and safety filters.",
                tool="Guardrails AI",
                phase=4,
                status="Integrated & Operational",
            ),
            PlannedModule(
                name="LLM Observability",
                key="langfuse",
                description="Complete tracing, latency profiling, token cost analytics, and production telemetry monitoring.",
                tool="Langfuse",
                phase=5,
                status="Integrated & Operational",
            ),
        ]

        return ProjectInfoResponse(
            name=settings.PROJECT_NAME,
            description="Professional enterprise platform for real-time evaluation, safety guardrails, and observability for Large Language Model applications.",
            version=settings.API_VERSION,
            current_phase="Phase 8: Live API Configuration, Integration Testing & Final Demonstration",
            framework="FastAPI + React Vite + Google GenAI SDK + DeepEval + Guardrails AI + Langfuse",
            planned_modules=modules,
            gemini_model=settings.GEMINI_MODEL,
            documentation_url="/docs",
        )
