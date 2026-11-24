"""Automated unit tests for LLMService and Gemini API integration using mocked responses."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

try:
    from app.services.llm_service import LLMService
    from app.models.schemas import ChatMessage, ChatResponse
    from app.core.config import settings
except ImportError:
    from backend.app.services.llm_service import LLMService
    from backend.app.models.schemas import ChatMessage, ChatResponse
    from backend.app.core.config import settings

from google.genai import errors


@pytest.fixture
def mock_llm_service():
    """Create a fresh instance of LLMService with reset metrics."""
    service = LLMService()
    service.reset_metrics()
    return service


def test_successful_gemini_response(mock_llm_service):
    """1. Test successful Gemini response generation."""
    mock_response = MagicMock()
    mock_response.text = "This is a successful response from Gemini."
    mock_response.usage_metadata.prompt_token_count = 12
    mock_response.usage_metadata.candidates_token_count = 28
    mock_response.usage_metadata.total_token_count = 40

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        res = mock_llm_service.generate_chat_response(message="Hello Gemini")

        assert isinstance(res, ChatResponse)
        assert res.response == "This is a successful response from Gemini."
        assert res.status == "success"
        assert res.model == settings.GEMINI_MODEL
        assert res.prompt_tokens == 12
        assert res.completion_tokens == 28
        assert res.total_tokens == 40
        assert res.latency_ms >= 0


def test_empty_message_validation(mock_llm_service):
    """2. Test that empty or whitespace messages raise HTTP 400."""
    with pytest.raises(HTTPException) as exc_info_empty:
        mock_llm_service.generate_chat_response(message="")
    assert exc_info_empty.value.status_code == 400
    assert "cannot be empty" in exc_info_empty.value.detail

    with pytest.raises(HTTPException) as exc_info_whitespace:
        mock_llm_service.generate_chat_response(message="   \n\t  ")
    assert exc_info_whitespace.value.status_code == 400


def test_missing_api_key_configuration(mock_llm_service):
    """3. Test missing or unconfigured GEMINI_API_KEY raises HTTP 500 when simulation is disabled."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with pytest.raises(HTTPException) as exc_info:
            mock_llm_service.generate_chat_response(message="Test prompt", allow_simulation=False)
        assert exc_info.value.status_code == 500
        assert "GEMINI_API_KEY is not configured" in exc_info.value.detail


def test_invalid_api_credentials(mock_llm_service):
    """4. Test that invalid API key errors raise HTTP 401."""
    mock_client = MagicMock()
    ce = errors.ClientError(400, {"error": {"message": "API_KEY_INVALID: API key not valid."}})
    mock_client.models.generate_content.side_effect = ce

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            mock_llm_service.generate_chat_response(message="Hello")
        assert exc_info.value.status_code == 401
        assert "Invalid Google AI Studio (Gemini) API key" in exc_info.value.detail


def test_gemini_api_failure(mock_llm_service):
    """5. Test upstream Gemini server / API error raises HTTP 502."""
    mock_client = MagicMock()
    ae = errors.APIError(503, {"error": {"message": "The service is temporarily overloaded."}})
    mock_client.models.generate_content.side_effect = ae

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            mock_llm_service.generate_chat_response(message="Hello")
        assert exc_info.value.status_code == 502
        assert "Gemini upstream API failure" in exc_info.value.detail


def test_token_metadata_extraction(mock_llm_service):
    """6. Test accurate extraction of token counts and null fallback when metadata is missing."""
    mock_response_with_tokens = MagicMock()
    mock_response_with_tokens.text = "Answer with tokens"
    mock_response_with_tokens.usage_metadata.prompt_token_count = 45
    mock_response_with_tokens.usage_metadata.candidates_token_count = 110
    mock_response_with_tokens.usage_metadata.total_token_count = 155

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response_with_tokens

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        res1 = mock_llm_service.generate_chat_response(message="Calculate tokens")
        assert res1.prompt_tokens == 45
        assert res1.completion_tokens == 110
        assert res1.total_tokens == 155

    # Case where usage_metadata is None (do not fabricate, return null)
    mock_response_no_tokens = MagicMock()
    mock_response_no_tokens.text = "Answer without tokens"
    mock_response_no_tokens.usage_metadata = None
    mock_client.models.generate_content.return_value = mock_response_no_tokens

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        res2 = mock_llm_service.generate_chat_response(message="No tokens")
        assert res2.prompt_tokens is None
        assert res2.completion_tokens is None
        assert res2.total_tokens is None


def test_latency_measurement(mock_llm_service):
    """7. Test latency measurement is tracked accurately and recorded."""
    mock_response = MagicMock()
    mock_response.text = "Timing response"
    mock_response.usage_metadata.prompt_token_count = 5
    mock_response.usage_metadata.candidates_token_count = 10
    mock_response.usage_metadata.total_token_count = 15

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        res = mock_llm_service.generate_chat_response(message="Measure speed")
        assert isinstance(res.latency_ms, float)
        assert res.latency_ms >= 0


def test_conversation_history_handling(mock_llm_service):
    """8. Test conversation history is properly formatted for Gemini types.Content."""
    mock_response = MagicMock()
    mock_response.text = "I remember our conversation."
    mock_response.usage_metadata.prompt_token_count = 20
    mock_response.usage_metadata.candidates_token_count = 15
    mock_response.usage_metadata.total_token_count = 35

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    history = [
        ChatMessage(role="user", content="My name is Alex."),
        ChatMessage(role="assistant", content="Nice to meet you Alex!"),
    ]

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        res = mock_llm_service.generate_chat_response(
            message="What is my name?",
            conversation_history=history,
        )

        assert res.response == "I remember our conversation."
        mock_client.models.generate_content.assert_called_once()
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        contents = call_kwargs["contents"]

        assert len(contents) == 3
        # Turn 1: user
        assert contents[0].role == "user"
        assert contents[0].parts[0].text == "My name is Alex."
        # Turn 2: assistant mapped to model
        assert contents[1].role == "model"
        assert contents[1].parts[0].text == "Nice to meet you Alex!"
        # Turn 3: current user message
        assert contents[2].role == "user"
        assert contents[2].parts[0].text == "What is my name?"


def test_telemetry_metrics_accumulation(mock_llm_service):
    """Test that actual Gemini calls update the real backend telemetry metrics."""
    mock_response = MagicMock()
    mock_response.text = "Telemetry output"
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.candidates_token_count = 20
    mock_response.usage_metadata.total_token_count = 30

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
        mock_llm_service.generate_chat_response(message="Req 1")
        mock_llm_service.generate_chat_response(message="Req 2")

    metrics = mock_llm_service.get_metrics()
    assert metrics.total_requests == 2
    assert metrics.total_tokens == 60
    assert metrics.average_latency_ms >= 0
    assert metrics.status == "operational"


def test_gemini_simulation_mode_unconfigured(mock_llm_service):
    """Phase 7: Test that unconfigured GEMINI_API_KEY cleanly generates a simulated response without fabricating tokens."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        res = mock_llm_service.generate_chat_response(message="What is RAG in conversational AI?")

        assert isinstance(res, ChatResponse)
        assert res.is_simulated is True
        assert res.status == "simulated"
        assert "Simulation Mode" in res.response
        assert "(Simulated)" in res.model
        assert res.prompt_tokens is None
        assert res.completion_tokens is None
        assert res.total_tokens is None
        assert res.trace_id is not None

        # Verify simulated request is not counted in live metrics
        metrics = mock_llm_service.get_metrics()
        assert metrics.total_requests == 0
        assert metrics.simulated_requests == 1
        assert metrics.total_tokens == 0


def test_simulation_and_live_metrics_separation(mock_llm_service):
    """Phase 7: Test that live Gemini calls and simulated calls maintain strictly separated metrics."""
    # 1. Execute a simulated response
    with patch.object(settings, "GEMINI_API_KEY", ""):
        mock_llm_service.generate_chat_response(message="Simulated query")

    # 2. Execute a live (mocked) Gemini response
    mock_response = MagicMock()
    mock_response.text = "Live verified response"
    mock_response.usage_metadata.prompt_token_count = 15
    mock_response.usage_metadata.candidates_token_count = 35
    mock_response.usage_metadata.total_token_count = 50

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "AIzaSyFakeKeyForTest"):
        with patch.object(mock_llm_service, "_get_client", return_value=mock_client):
            live_res = mock_llm_service.generate_chat_response(message="Live query")
            assert live_res.is_simulated is False
            assert live_res.status == "success"
            assert live_res.total_tokens == 50

    metrics = mock_llm_service.get_metrics()
    assert metrics.total_requests == 1
    assert metrics.simulated_requests == 1
    assert metrics.total_tokens == 50
