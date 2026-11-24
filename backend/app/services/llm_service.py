import time
import threading
from typing import List, Optional
from fastapi import HTTPException, status

try:
    from app.core.config import settings
    from app.models.schemas import ChatMessage, ChatResponse, MetricsResponse
    from app.services.guardrails_service import guardrails_service
    from app.services.observability_service import observability_service
except ImportError:
    from backend.app.core.config import settings
    from backend.app.models.schemas import ChatMessage, ChatResponse, MetricsResponse
    from backend.app.services.guardrails_service import guardrails_service
    from backend.app.services.observability_service import observability_service

from google import genai
from google.genai import types, errors


class LLMService:
    """Enterprise LLM Service managing Google Gemini API interactions,

    token metadata tracking, roundtrip latency measurement, and dashboard metrics.
    Supports clean separation between live Gemini execution and simulation mode.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._total_requests: int = 0
        self._simulated_requests: int = 0
        self._total_latency_ms: float = 0.0
        self._total_tokens: int = 0
        self._load_persisted_metrics()

    def _load_persisted_metrics(self) -> None:
        """Hydrate runtime metrics from persistent SQLite storage on startup."""
        try:
            with observability_service._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE eval_metric IS NULL AND status != 'simulated'"
                )
                self._total_requests = cursor.fetchone()[0] or 0

                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE eval_metric IS NULL AND status = 'simulated'"
                )
                self._simulated_requests = cursor.fetchone()[0] or 0

                cursor.execute(
                    "SELECT SUM(total_tokens) FROM observability_traces WHERE eval_metric IS NULL AND status != 'simulated'"
                )
                self._total_tokens = cursor.fetchone()[0] or 0

                cursor.execute(
                    "SELECT SUM(latency_ms) FROM observability_traces WHERE eval_metric IS NULL AND status IN ('success', 'sanitized') AND latency_ms > 0"
                )
                lat = cursor.fetchone()[0]
                self._total_latency_ms = float(lat) if lat is not None else 0.0
        except Exception:
            pass

    def is_api_configured(self) -> bool:
        """Check if a valid GEMINI_API_KEY is present in settings."""
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    def _get_client(self) -> genai.Client:
        """Initialize and return the Google GenAI client using configured credentials."""
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY is not configured. Please set your Google AI Studio API key in backend/.env.",
            )
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize Google GenAI client: {str(e)}",
            )

    def _record_metrics(self, latency_ms: float, tokens: Optional[int], is_simulated: bool = False) -> None:
        """Thread-safe update of backend telemetry metrics.

        Simulated calls are counted separately and do not distort live API metrics or tokens.
        """
        with self._lock:
            if is_simulated:
                self._simulated_requests += 1
            else:
                self._total_requests += 1
                self._total_latency_ms += latency_ms
                if tokens is not None and tokens > 0:
                    self._total_tokens += tokens

    def get_metrics(self) -> MetricsResponse:
        """Calculate and return actual operational metrics."""
        with self._lock:
            avg_latency = (
                round(self._total_latency_ms / self._total_requests, 2)
                if self._total_requests > 0
                else 0.0
            )
            return MetricsResponse(
                total_requests=self._total_requests,
                simulated_requests=self._simulated_requests,
                average_latency_ms=avg_latency,
                total_tokens=self._total_tokens,
                status="operational",
            )

    def reset_metrics(self) -> None:
        """Reset telemetry metrics for testing purposes."""
        with self._lock:
            self._total_requests = 0
            self._simulated_requests = 0
            self._total_latency_ms = 0.0
            self._total_tokens = 0

    def _generate_simulated_content(self, prompt: str) -> str:
        """Generate a structured simulated response when GEMINI_API_KEY is awaiting configuration."""
        snippet = prompt.strip()[:100] + ("..." if len(prompt.strip()) > 100 else "")
        return (
            "[Simulation Mode - Awaiting Google AI Studio Configuration]\n\n"
            "This response was generated in Simulation Mode because GEMINI_API_KEY is not configured in backend/.env.\n\n"
            f"Simulated analysis for your prompt:\n\"{snippet}\"\n\n"
            "• Engine Status: Simulation Pipeline Active (Internal Mock)\n"
            "• Safety Guardrails: Bidirectional inspection executed successfully\n"
            "• Observability: Trace logged locally as simulated telemetry\n"
            "• Live Execution: Provide a valid Google AI Studio API key at https://aistudio.google.com/ "
            "and set GEMINI_API_KEY in backend/.env to enable live Gemini inference."
        )

    def _build_contents(
        self, message: str, conversation_history: Optional[List[ChatMessage]] = None
    ) -> List[types.Content]:
        """Convert conversational turns into Gemini types.Content objects."""
        contents: List[types.Content] = []

        if conversation_history:
            for item in conversation_history:
                content_text = item.content.strip() if item.content else ""
                if not content_text:
                    continue

                # Normalize role: Gemini accepts 'user' and 'model'
                role = "model" if item.role in ["model", "assistant"] else "user"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content_text)],
                    )
                )

        # Append current user prompt
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
        )
        return contents

    def generate_chat_response(
        self,
        message: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        allow_simulation: bool = True,
    ) -> ChatResponse:
        """Execute bidirectional safety verification and Gemini LLM inference.

        1. Input Guardrails: Validate prompt for injection, jailbreak, toxicity, and integrity.
        2. If blocked: Halt immediately, log violation, and return safe rejection without calling Gemini.
        3. Simulation vs Live:
           - If GEMINI_API_KEY is configured: Calls live Google AI Studio API and records real token usage.
           - If unconfigured & allow_simulation=True: Generates structured simulated response with explicit indicators,
             does not increment live request count, does not fabricate token counts, and marks telemetry as simulated.
           - If unconfigured & allow_simulation=False: Raises HTTP 500 error requiring credentials.
        4. Output Guardrails: Verify generated response for toxicity, harmful content, and PII/secrets.
        5. If output blocked: Halt output disclosure and return safety warning.
        6. If sensitive data detected: Redact secrets/PII and return sanitized output.
        7. Otherwise: Return verified response with complete telemetry.
        """
        clean_message = message.strip() if message else ""
        if not clean_message:
            # Run input validation to record empty attempt in safety logs
            guardrails_service.validate_input(message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt message cannot be empty or whitespace.",
            )

        # ---------------------------------------------------------------------
        # 1. Input Guardrails Verification
        # ---------------------------------------------------------------------
        input_check = guardrails_service.validate_input(clean_message)
        if input_check.action == "BLOCK":
            # Record trace for blocked prompt
            trace_id = observability_service.record_llm_trace(
                name="gemini-chat-blocked",
                model=settings.GEMINI_MODEL or "gemini-3.5-flash-lite",
                latency_ms=0.0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                status="blocked",
                prompt=clean_message,
                error_message=input_check.reason,
                guardrail_status="BLOCK",
                risk_category=input_check.risk_category,
            )
            # Halts immediately: Blocked prompt NEVER reaches Gemini
            return ChatResponse(
                response=(
                    f"🛡️ Safety Guardrail Block: Your prompt was blocked because it triggered safety policies "
                    f"({input_check.risk_category}). Reason: {input_check.reason}"
                ),
                model=settings.GEMINI_MODEL or "gemini-3.5-flash-lite",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=0.0,
                status="blocked",
                guardrails_result=input_check.model_dump(),
                trace_id=trace_id,
                is_simulated=False,
            )

        # ---------------------------------------------------------------------
        # 2. Live Client Acquisition / Simulation Mode Fallback
        # ---------------------------------------------------------------------
        model_name = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        client = None
        is_live = False

        try:
            client = self._get_client()
            is_live = True
        except HTTPException as e:
            if e.status_code == 500 and "GEMINI_API_KEY is not configured" in str(e.detail):
                if not allow_simulation:
                    raise
                is_live = False
            else:
                raise

        if not is_live:
            start_time = time.perf_counter()
            simulated_text = self._generate_simulated_content(clean_message)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Run Output Guardrails on simulated content
            output_check = guardrails_service.validate_output(simulated_text)
            final_response_text = output_check.sanitized_text or simulated_text
            response_status = "sanitized" if output_check.action == "REDACT" else "simulated"

            # Record simulated metric (separate from real API traffic)
            self._record_metrics(elapsed_ms, tokens=None, is_simulated=True)

            # Record non-misleading simulated trace
            trace_id = observability_service.record_llm_trace(
                name="gemini-chat-simulated",
                model=f"{model_name} (Simulated)",
                latency_ms=elapsed_ms,
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                status="simulated",
                prompt=clean_message,
                response=final_response_text,
                guardrail_status=output_check.action,
                risk_category=output_check.risk_category,
            )

            return ChatResponse(
                response=final_response_text,
                model=f"{model_name} (Simulated)",
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                latency_ms=elapsed_ms,
                status=response_status,
                guardrails_result=output_check.model_dump(),
                trace_id=trace_id,
                is_simulated=True,
            )

        # ---------------------------------------------------------------------
        # 3. Live LLM Inference via Google Gemini API
        # ---------------------------------------------------------------------
        contents = self._build_contents(clean_message, conversation_history)
        model_name = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"

        start_time = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        except errors.ClientError as ce:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_msg = getattr(ce, "message", str(ce))
            error_code = getattr(ce, "code", None)

            observability_service.record_llm_trace(
                name="gemini-chat-error",
                model=model_name,
                latency_ms=elapsed_ms,
                status="error",
                prompt=clean_message,
                error_type="ClientError",
                error_message=error_msg,
            )

            # Check for credential / auth failure
            if error_code in [400, 401, 403] or "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google AI Studio (Gemini) API key. Please check your credentials.",
                )
            # Check for rate limiting
            elif error_code == 429 or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Gemini API rate limit or quota exceeded. Please try again later.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Gemini client error: {error_msg}",
                )

        except errors.APIError as ae:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_msg = getattr(ae, "message", str(ae))
            observability_service.record_llm_trace(
                name="gemini-chat-error",
                model=model_name,
                latency_ms=elapsed_ms,
                status="error",
                prompt=clean_message,
                error_type="APIError",
                error_message=error_msg,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini upstream API failure: {error_msg}",
            )

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            observability_service.record_llm_trace(
                name="gemini-chat-error",
                model=model_name,
                latency_ms=elapsed_ms,
                status="error",
                prompt=clean_message,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error communicating with Gemini API: {str(e)}",
            )

        # Extract actual response text
        response_text = ""
        if hasattr(response, "text") and response.text is not None:
            response_text = response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content and candidate.content.parts:
                response_text = "".join(
                    part.text for part in candidate.content.parts if hasattr(part, "text") and part.text
                ).strip()

        if not response_text:
            response_text = "No text content generated by the model."

        # Extract actual token usage metadata without fabrication
        prompt_tokens: Optional[int] = None
        completion_tokens: Optional[int] = None
        total_tokens: Optional[int] = None

        if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
            usage = response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)
            total_tokens = getattr(usage, "total_token_count", None)

        # Record operational metrics
        self._record_metrics(elapsed_ms, total_tokens)

        # ---------------------------------------------------------------------
        # 3. Output Guardrails Verification
        # ---------------------------------------------------------------------
        output_check = guardrails_service.validate_output(response_text)
        if output_check.action == "BLOCK":
            # Record trace for blocked output
            trace_id = observability_service.record_llm_trace(
                name="gemini-chat",
                model=model_name,
                latency_ms=elapsed_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                status="blocked",
                prompt=clean_message,
                guardrail_status="BLOCK",
                risk_category=output_check.risk_category,
            )
            # Halts disclosure: Unsafe response NEVER reaches React client
            return ChatResponse(
                response=(
                    f"🛡️ Safety Guardrail Block: The generated model response was blocked by output safety policies "
                    f"({output_check.risk_category})."
                ),
                model=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=elapsed_ms,
                status="blocked",
                guardrails_result=output_check.model_dump(),
                trace_id=trace_id,
                is_simulated=False,
            )

        final_response_text = output_check.sanitized_text or response_text
        response_status = "sanitized" if output_check.action == "REDACT" else "success"

        # Record full observability trace
        trace_id = observability_service.record_llm_trace(
            name="gemini-chat",
            model=model_name,
            latency_ms=elapsed_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            status=response_status,
            prompt=clean_message,
            response=final_response_text,
            guardrail_status=output_check.action,
            risk_category=output_check.risk_category,
        )

        return ChatResponse(
            response=final_response_text,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=elapsed_ms,
            status=response_status,
            guardrails_result=output_check.model_dump(),
            trace_id=trace_id,
            is_simulated=False,
        )


# Singleton LLM service instance
llm_service = LLMService()
