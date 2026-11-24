"""Direct unit tests for LLMGuard API endpoints."""

try:
    from app.main import root
    from app.api.endpoints import get_health, get_info
    from app.models.schemas import HealthResponse, ProjectInfoResponse
except ImportError:
    from backend.app.main import root
    from backend.app.api.endpoints import get_health, get_info
    from backend.app.models.schemas import HealthResponse, ProjectInfoResponse


def test_root_endpoint_direct():
    result = root()
    assert "LLMGuard" in result["message"]
    assert result["status"] == "online"
    assert result["health_endpoint"] == "/api/health"
    assert result["chat_endpoint"] == "/api/chat"


def test_health_endpoint_direct():
    health = get_health()
    assert isinstance(health, HealthResponse)
    assert health.status == "healthy"
    assert "LLMGuard" in health.app_name
    assert health.version == "0.8.0"
    assert health.environment == "development"
    assert bool(health.timestamp) is True


def test_info_endpoint_direct():
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
