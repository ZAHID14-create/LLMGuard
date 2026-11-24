import os
import re
import uuid
import sqlite3
import threading
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

try:
    from app.core.config import settings
    from app.models.schemas import (
        TraceItem,
        ObservabilitySummaryResponse,
        ObservabilityHistoryResponse,
        ObservabilityStatusResponse,
    )
except ImportError:
    from backend.app.core.config import settings
    from backend.app.models.schemas import (
        TraceItem,
        ObservabilitySummaryResponse,
        ObservabilityHistoryResponse,
        ObservabilityStatusResponse,
    )

try:
    from langfuse import Langfuse
except ImportError:
    Langfuse = None


class ObservabilityService:
    """Enterprise LLM Observability & Tracing Service.

    Integrates with Langfuse Cloud SDK for telemetry, generation tracing,
    token tracking, and latency profiling, while maintaining privacy-preserving
    local SQLite audit records.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        client: Optional[Any] = None,
    ):
        self.db_path = db_path or settings.GUARDRAILS_DB_PATH
        self._custom_public_key = public_key
        self._custom_secret_key = secret_key
        self._custom_base_url = base_url
        self._lock = threading.Lock()
        self._last_trace_timestamp: Optional[str] = None
        self._client: Optional[Any] = client
        self._connection_status: str = "Connected" if client is not None else "Not Configured"
        self._is_configured: bool = client is not None
        self._init_error: Optional[str] = None

        self._ensure_db_directory()
        self._init_db()
        if client is None:
            self._init_langfuse_client()

    def _ensure_db_directory(self) -> None:
        """Ensure database parent directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with timeout and dictionary row factory."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize the local observability_traces table."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS observability_traces (
                        trace_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        name TEXT NOT NULL,
                        model TEXT,
                        latency_ms REAL NOT NULL,
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        total_tokens INTEGER,
                        status TEXT NOT NULL,
                        error_type TEXT,
                        error_message TEXT,
                        guardrail_status TEXT,
                        risk_category TEXT,
                        eval_metric TEXT,
                        eval_score REAL,
                        is_remote INTEGER NOT NULL
                    );
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_status ON observability_traces(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_ts ON observability_traces(timestamp);")
                conn.commit()

    def _init_langfuse_client(self) -> None:
        """Initialize official Langfuse SDK client if credentials are configured."""
        public_key = (
            self._custom_public_key
            if self._custom_public_key is not None
            else (settings.LANGFUSE_PUBLIC_KEY.strip() if settings.LANGFUSE_PUBLIC_KEY else "")
        )
        secret_key = (
            self._custom_secret_key
            if self._custom_secret_key is not None
            else (settings.LANGFUSE_SECRET_KEY.strip() if settings.LANGFUSE_SECRET_KEY else "")
        )
        base_url = (
            self._custom_base_url
            if self._custom_base_url is not None
            else settings.canonical_langfuse_host
        )

        if not public_key or not secret_key or Langfuse is None:
            self._client = None
            self._is_configured = False
            self._connection_status = "Not Configured"
            return

        self._is_configured = True
        try:
            self._client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=base_url,
            )
            # Verify connectivity with Langfuse Cloud
            if self._client.auth_check():
                self._connection_status = "Connected"
            else:
                self._connection_status = "Connection Error"
        except Exception as e:
            # Fallback gracefully if network resolution or key verification fails
            self._connection_status = "Connection Error"
            self._init_error = str(e)

    def _sanitize_trace_content(self, text: Optional[str], max_len: int = 250) -> str:
        """Sanitize strings for observability logs by removing credentials and truncating."""
        if not text:
            return ""
        # Strip API keys and credentials
        sanitized = re.sub(r"\bAIza[0-9A-Za-z\-_]{15,60}\b", "[REDACTED_API_KEY]", text)
        sanitized = re.sub(r"\bsk-[A-Za-z0-9\-_]{16,}\b", "[REDACTED_API_KEY]", sanitized)
        sanitized = re.sub(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b", "[REDACTED_API_KEY]", sanitized)
        sanitized = re.sub(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b", "[REDACTED_EMAIL]", sanitized)
        sanitized = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]", sanitized)
        sanitized = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", sanitized)
        sanitized = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[REDACTED_CC]", sanitized)
        sanitized = " ".join(sanitized.split())
        return sanitized[:max_len] + ("..." if len(sanitized) > max_len else "")

    _sanitize_for_trace = _sanitize_trace_content

    # -------------------------------------------------------------------------
    # Core Tracing API
    # -------------------------------------------------------------------------

    def record_llm_trace(
        self,
        name: str = "gemini-chat",
        model: Optional[str] = "gemini-3.5-flash-lite",
        latency_ms: float = 0.0,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        status: str = "success",
        prompt: Optional[str] = None,
        response: Optional[str] = None,
        response_text: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        guardrail_status: Optional[str] = None,
        risk_category: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> str:
        """Record an LLM request execution trace to local SQLite and dispatch to Langfuse Cloud."""
        if response is None and response_text is not None:
            response = response_text

        assigned_trace_id = trace_id or f"trace_{uuid.uuid4().hex[:12]}"
        now_ts = datetime.now(timezone.utc).isoformat()
        self._last_trace_timestamp = now_ts
        is_remote_synced = False
        sanitized_error = self._sanitize_trace_content(error_message) if error_message else None

        # If Langfuse is configured, dispatch remote observation event
        if self._client and self._connection_status == "Connected":
            try:
                sanitized_input = self._sanitize_trace_content(prompt)
                sanitized_output = self._sanitize_trace_content(response)

                # Send observation event / trace to Langfuse Cloud
                self._client.create_event(
                    name=name,
                    metadata={
                        "trace_id": assigned_trace_id,
                        "model": model,
                        "latency_ms": latency_ms,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "status": status,
                        "error_type": error_type,
                        "guardrail_status": guardrail_status,
                        "risk_category": risk_category,
                        "input_preview": sanitized_input,
                        "output_preview": sanitized_output,
                    },
                )
                # Flush asynchronous batch buffer
                if hasattr(self._client, "flush"):
                    self._client.flush()
                is_remote_synced = True
            except Exception:
                is_remote_synced = False

        # Store minimal, non-sensitive audit metadata in local SQLite
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO observability_traces (
                        trace_id, timestamp, name, model, latency_ms,
                        prompt_tokens, completion_tokens, total_tokens,
                        status, error_type, error_message, guardrail_status,
                        risk_category, eval_metric, eval_score, is_remote
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assigned_trace_id,
                        now_ts,
                        name,
                        model,
                        latency_ms,
                        prompt_tokens,
                        completion_tokens,
                        total_tokens,
                        status,
                        error_type,
                        sanitized_error,
                        guardrail_status,
                        risk_category,
                        None,
                        None,
                        1 if is_remote_synced else 0,
                    ),
                )
                conn.commit()

        return assigned_trace_id

    def record_evaluation_event(
        self,
        evaluation_id: str,
        metric: str,
        score: float,
        risk: Optional[float] = None,
        status: str = "passed",
        latency_ms: float = 0.0,
    ) -> str:
        """Record DeepEval LLM evaluation execution to observability telemetry."""
        assigned_trace_id = f"eval_{uuid.uuid4().hex[:12]}"
        now_ts = datetime.now(timezone.utc).isoformat()
        self._last_trace_timestamp = now_ts
        is_remote_synced = False

        if self._client and self._connection_status == "Connected":
            try:
                self._client.create_event(
                    name=f"deepeval-{metric}",
                    metadata={
                        "evaluation_id": evaluation_id,
                        "metric": metric,
                        "score": score,
                        "risk": risk,
                        "status": status,
                        "trace_id": assigned_trace_id,
                    },
                )
                if hasattr(self._client, "flush"):
                    self._client.flush()
                is_remote_synced = True
            except Exception:
                is_remote_synced = False

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO observability_traces (
                        trace_id, timestamp, name, model, latency_ms,
                        prompt_tokens, completion_tokens, total_tokens,
                        status, error_type, error_message, guardrail_status,
                        risk_category, eval_metric, eval_score, is_remote
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assigned_trace_id,
                        now_ts,
                        f"deepeval-{metric}",
                        settings.EVALUATION_MODEL or "gemini-3.5-flash-lite",
                        latency_ms,
                        None,
                        None,
                        None,
                        status,
                        None,
                        f"Evaluation ID: {evaluation_id}",
                        None,
                        None,
                        metric,
                        score,
                        1 if is_remote_synced else 0,
                    ),
                )
                conn.commit()

        return assigned_trace_id

    # -------------------------------------------------------------------------
    # Aggregation & Status APIs
    # -------------------------------------------------------------------------

    def get_summary(self) -> ObservabilitySummaryResponse:
        """Compute real aggregate metrics across all recorded local and remote traces."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM observability_traces")
                total_traces = cursor.fetchone()[0]

                # Filter out evaluation runs (eval_metric IS NULL) so only real LLM requests are counted here
                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE eval_metric IS NULL AND status IN ('success', 'sanitized')"
                )
                successful_requests = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE eval_metric IS NULL AND status IN ('error', 'blocked', 'failed')"
                )
                failed_requests = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE eval_metric IS NULL AND status != 'simulated'"
                )
                total_llm_requests = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE eval_metric IS NULL AND status = 'simulated'"
                )
                simulated_requests = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE is_remote = 1"
                )
                cloud_synced_traces = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM observability_traces WHERE is_remote = 0"
                )
                local_only_traces = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT AVG(latency_ms) FROM observability_traces WHERE eval_metric IS NULL AND latency_ms > 0"
                )
                avg_lat_row = cursor.fetchone()[0]
                average_latency_ms = round(avg_lat_row, 2) if avg_lat_row is not None else 0.0

                cursor.execute(
                    "SELECT SUM(prompt_tokens), SUM(completion_tokens), SUM(total_tokens) FROM observability_traces WHERE eval_metric IS NULL AND status != 'simulated'"
                )
                tokens_row = cursor.fetchone()
                total_in = tokens_row[0] or 0
                total_out = tokens_row[1] or 0
                total_tokens = tokens_row[2] or 0

                return ObservabilitySummaryResponse(
                    total_traces=total_traces,
                    successful_requests=successful_requests,
                    failed_requests=failed_requests,
                    average_latency_ms=average_latency_ms,
                    total_input_tokens=total_in,
                    total_output_tokens=total_out,
                    total_tokens_consumed=total_tokens,
                    connection_status=self._connection_status,
                    is_configured=self._is_configured,
                    total_llm_requests=total_llm_requests,
                    simulated_requests=simulated_requests,
                    cloud_synced_traces=cloud_synced_traces,
                    local_only_traces=local_only_traces,
                )

    def get_history(self, limit: int = 50, offset: int = 0, status_filter: Optional[str] = None) -> ObservabilityHistoryResponse:
        """Retrieve recent chronological traces from local audit storage."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                conditions = []
                params: List[Any] = []
                if status_filter:
                    conditions.append("status = ?")
                    params.append(status_filter.lower())

                where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

                count_q = f"SELECT COUNT(*) FROM observability_traces {where_clause}"
                cursor.execute(count_q, params)
                total = cursor.fetchone()[0]

                query = f"""
                    SELECT trace_id, timestamp, name, model, latency_ms,
                           prompt_tokens, completion_tokens, total_tokens,
                           status, error_type, error_message, guardrail_status,
                           risk_category, eval_metric, eval_score, is_remote
                    FROM observability_traces
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """
                cursor.execute(query, params + [limit, offset])
                rows = cursor.fetchall()

                traces = [
                    TraceItem(
                        trace_id=row["trace_id"],
                        timestamp=row["timestamp"],
                        name=row["name"],
                        model=row["model"],
                        latency_ms=row["latency_ms"],
                        prompt_tokens=row["prompt_tokens"],
                        completion_tokens=row["completion_tokens"],
                        total_tokens=row["total_tokens"],
                        status=row["status"],
                        error_type=row["error_type"],
                        error_message=row["error_message"],
                        guardrail_status=row["guardrail_status"],
                        risk_category=row["risk_category"],
                        eval_metric=row["eval_metric"],
                        eval_score=row["eval_score"],
                        is_remote=bool(row["is_remote"]),
                    )
                    for row in rows
                ]

                return ObservabilityHistoryResponse(total=total, traces=traces)

    def get_status(self) -> ObservabilityStatusResponse:
        """Provide detailed Langfuse connection status and configuration guidance."""
        base_url = settings.canonical_langfuse_host

        if not self._is_configured:
            guidance = (
                "Langfuse is not configured. Add LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, "
                "and LANGFUSE_BASE_URL to backend/.env to stream traces to Langfuse Cloud. "
                "Local SQLite observability is active and capturing all requests."
            )
        elif self._connection_status == "Connected":
            guidance = f"Langfuse Cloud connection verified at {base_url}. Remote trace ingestion active."
        else:
            guidance = (
                f"Langfuse credentials provided, but connection to {base_url} failed. "
                "Check network access and API key permissions. Fallback to local tracing active."
            )

        return ObservabilityStatusResponse(
            is_configured=self._is_configured,
            sdk_initialized=self._client is not None,
            connection_status=self._connection_status,
            base_url=base_url,
            last_trace_timestamp=self._last_trace_timestamp,
            guidance=guidance,
        )

    def clear_traces(self) -> None:
        """Clear all stored traces (used for unit testing isolation)."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM observability_traces")
                conn.commit()


# Singleton Instance
observability_service = ObservabilityService()
