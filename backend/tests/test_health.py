"""Pytest test suite for LLMGuard API endpoints."""

try:
    from app.main import root, app
    from app.api.endpoints import get_health, get_info
    from app.models.schemas import HealthResponse, ProjectInfoResponse
except ImportError:
    from backend.app.main import root, app
    from backend.app.api.endpoints import get_health, get_info
    from backend.app.models.schemas import HealthResponse, ProjectInfoResponse


def test_app_initialization():
    assert app.title == "LLMGuard – AI Evaluation & Safety Monitoring Platform"
    assert app.version == "0.8.0"


def test_root_endpoint():
    response = root()
    assert "LLMGuard" in response["message"]
    assert response["status"] == "online"
    assert response["documentation"] == "/docs"
    assert response["health_endpoint"] == "/api/health"
    assert response["info_endpoint"] == "/api/info"
    assert response["chat_endpoint"] == "/api/chat"
    assert response["metrics_endpoint"] == "/api/metrics"


def test_health_endpoint():
    health = get_health()
    assert isinstance(health, HealthResponse)
    assert health.status == "healthy"
    assert "LLMGuard" in health.app_name
    assert health.version == "0.8.0"
    assert health.environment == "development"
    assert health.timestamp is not None


def test_info_endpoint():
    info = get_info()
    assert isinstance(info, ProjectInfoResponse)
    assert "LLMGuard" in info.name
    assert "Phase 8" in info.current_phase
    assert len(info.planned_modules) == 4

    keys = [m.key for m in info.planned_modules]
    assert "gemini_llm" in keys
    assert "deepeval" in keys
    assert "guardrails_ai" in keys
    assert "langfuse" in keys
