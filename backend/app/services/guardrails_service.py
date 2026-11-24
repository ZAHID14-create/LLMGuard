import os
import re
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any

# Disable telemetry and external network exports
os.environ["GUARDRAILS_TELEMETRY"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

try:
    from app.core.config import settings
    from app.models.schemas import (
        GuardrailsCheckResponse,
        GuardrailsSummaryResponse,
        GuardrailsLogItem,
        GuardrailsHistoryResponse,
    )
except ImportError:
    from backend.app.core.config import settings
    from backend.app.models.schemas import (
        GuardrailsCheckResponse,
        GuardrailsSummaryResponse,
        GuardrailsLogItem,
        GuardrailsHistoryResponse,
    )

import guardrails
from guardrails import Guard
from guardrails.validator_base import (
    Validator,
    PassResult,
    FailResult,
    ValidationResult,
    register_validator,
)


# =============================================================================
# Custom Guardrails AI Validators
# =============================================================================

@register_validator(name="llmguard/prompt_injection", data_type="string")
class PromptInjectionValidator(Validator):
    """Detects prompt injection attempts aiming to override or reveal system prompts."""

    INJECTION_PATTERNS = [
        re.compile(r"(?i)\b(ignore|forget|disregard|overwrite|bypass|clear|drop)\s+(all\s+)?(previous|past|above|prior|initial)\s+(instructions|directives|prompts|rules|commands)\b"),
        re.compile(r"(?i)\b(reveal|show|display|print|expose|output|dump)\s+(the\s+)?(system|internal|hidden|secret|initial)\s+(prompt|instructions|rules|pre-prompt)\b"),
        re.compile(r"(?i)\b(system\s+prompt|developer\s+mode|administrative\s+override|sudo\s+mode)\b"),
        re.compile(r"(?i)(---\s*BEGIN\s+SYSTEM|\[SYSTEM\]|system\s*:\s*|human\s*:\s*|assistant\s*:\s*|<\|im_start\|>|<\|im_end\|>)"),
        re.compile(r"(?i)\b(print\s+everything\s+above|repeat\s+the\s+words\s+above)\b"),
        re.compile(r"(?i)\b(bypass\s+(all\s+)?safety\s+(filters|rules|guardrails))\b"),
    ]

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        for pattern in self.INJECTION_PATTERNS:
            match = pattern.search(value)
            if match:
                return FailResult(
                    error_message=f"Prompt injection pattern detected: '{match.group(0)}'",
                    fix_value=None,
                )
        return PassResult()


@register_validator(name="llmguard/jailbreak", data_type="string")
class JailbreakValidator(Validator):
    """Detects jailbreak personas (e.g. DAN, evil bot) attempting to break safety guardrails."""

    JAILBREAK_PATTERNS = [
        re.compile(r"(?i)\b(dan|do\s+anything\s+now|jailbreak|jailbroken|unfiltered\s+ai|evil\s+bot|no\s+morals|no\s+ethics|unrestricted\s+mode|break\s+the\s+rules|pretend\s+you\s+can\s+do\s+anything)\b"),
        re.compile(r"(?i)\b(you\s+are\s+now\s+free\s+from|ignore\s+all\s+ethical|disregard\s+all\s+content\s+policies|act\s+as\s+an\s+unfiltered|you\s+must\s+never\s+refuse)\b"),
        re.compile(r"(?i)\b(in\s+a\s+hypothetical\s+world\s+where\s+laws\s+don['']?t\s+exist|for\s+educational\s+purposes\s+only\s+how\s+to\s+(hack|attack|steal|harm))\b"),
        re.compile(r"(?i)\b(switch\s+to\s+unfiltered|enable\s+god\s+mode|disable\s+all\s+filters)\b"),
    ]

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        for pattern in self.JAILBREAK_PATTERNS:
            match = pattern.search(value)
            if match:
                return FailResult(
                    error_message=f"Jailbreak pattern detected: '{match.group(0)}'",
                    fix_value=None,
                )
        return PassResult()


@register_validator(name="llmguard/toxicity", data_type="string")
class ToxicityValidator(Validator):
    """Detects toxic, threatening, abusive, or hate speech language."""

    TOXICITY_PATTERNS = [
        re.compile(r"(?i)\b(i\s+will\s+(kill|murder|bomb|stab|attack|destroy|hurt|assassinate)|go\s+kill\s+yourself|hope\s+you\s+die)\b"),
        re.compile(r"(?i)\b(you\s+are\s+(a\s+piece\s+of\s+shit|retarded|an\s+idiot|scum|worthless))\b"),
        re.compile(r"(?i)\b(kill\s+all\s+(humans|men|women|infidels))\b"),
        re.compile(r"(?i)\b(fucking\s+(bastard|moron|cunt|bitch|whore))\b"),
    ]

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        for pattern in self.TOXICITY_PATTERNS:
            match = pattern.search(value)
            if match:
                return FailResult(
                    error_message=f"Toxic or abusive language detected: '{match.group(0)}'",
                    fix_value=None,
                )
        return PassResult()


@register_validator(name="llmguard/threat_generation", data_type="string")
class ThreatGenerationValidator(Validator):
    """Detects requests that ask an AI system to create threatening, intimidating,
    harassing, coercive, or violent messages against people.
    """

    PATTERNS = [
        # 1. Explicit request to write/create/generate a threatening, intimidating, harassing, violent, or coercive message
        re.compile(
            r"(?i)\b(write|generate|create|draft|compose|produce|formulate|craft|make|author|give\s+me|send)\b.*?"
            r"\b(threatening|intimidat\w+|harassing|violent|coercive|blackmail|extortion)\b.*?"
            r"\b(message|text|email|letter|note|statement|post|dm|communication|threat)\b"
        ),
        # 2. Request to write/create a message/threat with intent to intimidate/scare/coerce/threaten/hurt/blackmail/force
        re.compile(
            r"(?i)\b(write|generate|create|draft|compose|produce|formulate|craft|make|author|give\s+me|send)\b.*?"
            r"\b(message|text|email|letter|note|statement|communication|threat|words)\b.*?"
            r"\b(to|intended\s+to|designed\s+to|meant\s+to)\b.*?"
            r"\b(intimidate|scare|frighten|coerce|threaten|hurt|harm|blackmail|terrorize|extort|force\s+\w+\s+to\s+(comply|obey))\b"
        ),
        # 3. Request to write/create a message threatening harm, violence, death, or injury
        re.compile(
            r"(?i)\b(write|generate|create|draft|compose|produce|formulate|craft)\b.*?"
            r"\b(message|text|email|letter|note)\b.*?"
            r"\bthreatening\s+(to\s+(hurt|harm|kill|injure|attack|destroy|damage|retaliate)|violence|harm|death|injury)\b"
        ),
        # 4. Generate/create a violent threat / threat against another person
        re.compile(
            r"(?i)\b(write|generate|create|draft|compose|produce|formulate|craft)\b.*?"
            r"\b(a\s+)?(violent\s+threat|threat\s+of\s+violence|threat\s+against\s+(another\s+person|someone|somebody|people|a\s+person))\b"
        ),
        # 5. Direct requests to threaten/intimidate/coerce someone into compliance
        re.compile(
            r"(?i)\b(how\s+can\s+i|help\s+me|tell\s+me\s+how\s+to)\s+(threaten|intimidate|scare|frighten|coerce|harass)\s+(someone|somebody|another\s+person|my\s+\w+)\s+(into|to\s+make\s+them|so\s+they)\b"
        ),
    ]

    # Contextual whitelist to prevent false positives on harmless educational, cybersecurity, psychological, or defensive questions
    EDUCATIONAL_WHITELIST = [
        re.compile(
            r"(?i)\b(what\s+is|what\s+are|how\s+does|how\s+do|how\s+can\s+people\s+respond|explain\s+how|define|psychology\s+of|history\s+of|overview\s+of)\b.*?"
            r"\b(cybersecurity|threat\s+detection|threat\s+modeling|threat\s+intelligence|advanced\s+persistent|apt|mitigation|safely\s+to|psychology|threatening\s+behaviou?r)\b"
        ),
        re.compile(
            r"(?i)\b(how\s+can\s+(people|individuals|victims|users|employees)\s+respond\s+safely\s+to\s+(intimidation|threats|harassment))\b"
        ),
        re.compile(
            r"(?i)\b(explain\s+the\s+psychology\s+of\s+threatening\s+behaviou?r)\b"
        ),
    ]

    @classmethod
    def detect(cls, text: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(text, str):
            return False, None
        for whitelist in cls.EDUCATIONAL_WHITELIST:
            if whitelist.search(text):
                return False, None
        for pattern in cls.PATTERNS:
            match = pattern.search(text)
            if match:
                return True, match.group(0)
        return False, None

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        is_threat, match_snippet = self.detect(value)
        if is_threat:
            return FailResult(
                error_message="Request to generate threatening or intimidating content.",
                fix_value=None,
            )
        return PassResult()


@register_validator(name="llmguard/sensitive_data", data_type="string")
class SensitiveDataValidator(Validator):
    """Detects personal identifiable info (PII) and exposed credentials."""

    API_KEY_PATTERNS = [
        ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{15,60}\b")),
        ("OpenAI API Key", re.compile(r"\bsk-[A-Za-z0-9\-_]{16,}\b")),
        ("GitHub Token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
        ("Private Key", re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----")),
        ("Bearer Token", re.compile(r"Bearer\s+[A-Za-z0-9\-_]{24,}")),
    ]

    PII_PATTERNS = [
        ("Social Security Number", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
        ("Credit Card", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")),
        ("Email Address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
        ("Phone Number", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ]

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        if not isinstance(value, str):
            return PassResult()
        for name, pattern in self.API_KEY_PATTERNS:
            match = pattern.search(value)
            if match:
                return FailResult(
                    error_message=f"Credential exposure detected: {name}",
                    fix_value=None,
                )
        for name, pattern in self.PII_PATTERNS:
            match = pattern.search(value)
            if match:
                return FailResult(
                    error_message=f"Sensitive PII detected: {name}",
                    fix_value=None,
                )
        return PassResult()


# =============================================================================
# Guardrails Service Implementation
# =============================================================================

class GuardrailsService:
    """Enterprise AI Safety & Moderation Service.

    Coordinates input prompt inspection, output verification, SQLite safety logs,
    and Guardrails AI validator pipelines.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.GUARDRAILS_DB_PATH
        self._lock = threading.Lock()
        self._ensure_db_directory()
        self._init_db()

        # Initialize Guardrails AI Guards
        try:
            self._input_guard = Guard().use(
                PromptInjectionValidator(on_fail="noop"),
                JailbreakValidator(on_fail="noop"),
                ThreatGenerationValidator(on_fail="noop"),
                ToxicityValidator(on_fail="noop"),
            )
            self._output_guard = Guard().use(
                ToxicityValidator(on_fail="noop"),
                SensitiveDataValidator(on_fail="noop"),
            )
        except Exception:
            # Fallback if Guard instantiation issues occur
            self._input_guard = None
            self._output_guard = None

    def _ensure_db_directory(self) -> None:
        """Create parent directory for SQLite database if it doesn't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with timeout and dictionary row factory."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize the persistent SQLite safety_logs table."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS safety_logs (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        validation_type TEXT NOT NULL,
                        risk_category TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        action TEXT NOT NULL,
                        validation_reason TEXT NOT NULL,
                        detected_issues TEXT NOT NULL,
                        input_snippet TEXT NOT NULL,
                        status TEXT NOT NULL
                    );
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_action ON safety_logs(action);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON safety_logs(timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON safety_logs(validation_type);")
                conn.commit()

    def _sanitize_snippet(self, text: str, max_length: int = 100) -> str:
        """Sanitize and truncate text snippet for audit logs without exposing secrets."""
        if not text:
            return ""
        # Mask any potential API key or secret before saving to log
        sanitized = re.sub(r"\bAIza[0-9A-Za-z\-_]{15,60}\b", "[REDACTED_KEY]", text)
        sanitized = re.sub(r"\bsk-[A-Za-z0-9\-_]{16,}\b", "[REDACTED_KEY]", sanitized)
        sanitized = re.sub(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b", "[REDACTED_KEY]", sanitized)
        sanitized = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", sanitized)
        sanitized = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[REDACTED_CC]", sanitized)
        sanitized = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]", sanitized)
        sanitized = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]", sanitized)
        sanitized = " ".join(sanitized.split())
        return sanitized[:max_length] + ("..." if len(sanitized) > max_length else "")

    def _insert_log(
        self,
        validation_type: str,
        risk_category: str,
        severity: str,
        action: str,
        validation_reason: str,
        detected_issues: List[str],
        raw_text: str,
        status_val: str,
    ) -> str:
        """Insert a safety verification log into SQLite database."""
        record_id = f"sec_{uuid.uuid4().hex[:10]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        snippet = self._sanitize_snippet(raw_text)

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO safety_logs (
                        id, timestamp, validation_type, risk_category,
                        severity, action, validation_reason, detected_issues,
                        input_snippet, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record_id,
                        timestamp,
                        validation_type,
                        risk_category,
                        severity,
                        action,
                        validation_reason,
                        json.dumps(detected_issues),
                        snippet,
                        status_val,
                    ),
                )
                conn.commit()
        return record_id

    # -------------------------------------------------------------------------
    # Input Validation
    # -------------------------------------------------------------------------

    def validate_input(self, text: Optional[str], persist_log: bool = True) -> GuardrailsCheckResponse:
        """Evaluate an input prompt against integrity, injection, jailbreak, and toxicity rules."""
        # 1. Empty / Whitespace check
        if text is None or not text.strip():
            record_id = None
            reason = "Input validation failed: Prompt cannot be empty or solely whitespace."
            if persist_log:
                record_id = self._insert_log(
                    validation_type="input",
                    risk_category="Input Validation",
                    severity="Low",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=["empty_input"],
                    raw_text=text or "",
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Input Validation",
                severity="Low",
                reason=reason,
                detected_issues=["empty_input"],
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 2. Length check
        if len(text) > settings.MAX_INPUT_LENGTH:
            record_id = None
            reason = (
                f"Input validation failed: Prompt length ({len(text)} characters) "
                f"exceeds maximum allowed threshold of {settings.MAX_INPUT_LENGTH} characters."
            )
            if persist_log:
                record_id = self._insert_log(
                    validation_type="input",
                    risk_category="Input Validation",
                    severity="Medium",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=["excessive_length"],
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Input Validation",
                severity="Medium",
                reason=reason,
                detected_issues=["excessive_length"],
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 3. Control / binary characters
        if "\x00" in text:
            record_id = None
            reason = "Input validation failed: Prompt contains invalid null or binary control characters."
            if persist_log:
                record_id = self._insert_log(
                    validation_type="input",
                    risk_category="Input Validation",
                    severity="Medium",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=["malformed_characters"],
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Input Validation",
                severity="Medium",
                reason=reason,
                detected_issues=["malformed_characters"],
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 4. Guardrails AI Official Engine Validation (Prompt Injection, Jailbreak, Toxicity)
        if self._input_guard is not None:
            try:
                outcome = self._input_guard.validate(text)
                if not outcome.validation_passed:
                    summaries = getattr(outcome, "validation_summaries", [])
                    detected = []
                    fail_reasons = []
                    for s in summaries:
                        detected.append(getattr(s, "validator_name", "Validator"))
                        fail_reasons.append(getattr(s, "failure_reason", "Validation check failed"))

                    category = "Prompt Injection"
                    severity = "High"
                    if any("Jailbreak" in d for d in detected):
                        category = "Jailbreak"
                        severity = "Critical"
                    elif any("ThreatGeneration" in d for d in detected):
                        category = "Threat Generation / Harmful Content"
                        severity = "High"
                    elif any("Toxicity" in d for d in detected):
                        category = "Toxicity"
                        severity = "High"

                    if category == "Threat Generation / Harmful Content":
                        reason = "Request to generate threatening or intimidating content."
                        detected_list = ["Request to generate threatening or intimidating content."]
                    else:
                        reason = "; ".join(fail_reasons) if fail_reasons else f"Security policy violation intercepted by Guardrails AI ({category})."
                        detected_list = detected or [category]

                    record_id = None
                    if persist_log:
                        record_id = self._insert_log(
                            validation_type="input",
                            risk_category=category,
                            severity=severity,
                            action="BLOCK",
                            validation_reason=reason,
                            detected_issues=detected_list,
                            raw_text=text,
                            status_val="failed",
                        )
                    return GuardrailsCheckResponse(
                        validation_status="failed",
                        action="BLOCK",
                        risk_category=category,
                        severity=severity,
                        reason=reason,
                        detected_issues=detected_list,
                        record_id=record_id,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
            except Exception as e:
                # Fail-safe principle: Never silently bypass on internal error
                record_id = None
                reason = f"Fail-safe block: Safety verification encountered an internal error ({str(e)})."
                if persist_log:
                    record_id = self._insert_log(
                        validation_type="input",
                        risk_category="System Error",
                        severity="High",
                        action="BLOCK",
                        validation_reason=reason,
                        detected_issues=["guardrails_engine_error"],
                        raw_text=text,
                        status_val="failed",
                    )
                return GuardrailsCheckResponse(
                    validation_status="failed",
                    action="BLOCK",
                    risk_category="System Error",
                    severity="High",
                    reason=reason,
                    detected_issues=["guardrails_engine_error"],
                    record_id=record_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        # 5. Secondary Heuristic Defense-in-Depth Layer
        injection_matches = []
        for pattern in PromptInjectionValidator.INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                injection_matches.append(match.group(0))

        if injection_matches:
            record_id = None
            reason = (
                "Prompt injection attempt detected: Input attempts to override, circumvent, "
                "or disclose system instructions."
            )
            if persist_log:
                record_id = self._insert_log(
                    validation_type="input",
                    risk_category="Prompt Injection",
                    severity="High",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=injection_matches,
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Prompt Injection",
                severity="High",
                reason=reason,
                detected_issues=injection_matches,
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 5. Jailbreak Detection
        jailbreak_matches = []
        for pattern in JailbreakValidator.JAILBREAK_PATTERNS:
            match = pattern.search(text)
            if match:
                jailbreak_matches.append(match.group(0))

        if jailbreak_matches:
            record_id = None
            reason = (
                "Jailbreak attempt detected: Input attempts to induce unrestricted, "
                "adversarial, or unauthorized model persona."
            )
            if persist_log:
                record_id = self._insert_log(
                    validation_type="input",
                    risk_category="Jailbreak",
                    severity="Critical",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=jailbreak_matches,
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Jailbreak",
                severity="Critical",
                reason=reason,
                detected_issues=jailbreak_matches,
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 6. Toxicity Detection
        toxic_matches = []
        for pattern in ToxicityValidator.TOXICITY_PATTERNS:
            match = pattern.search(text)
            if match:
                toxic_matches.append(match.group(0))

        if toxic_matches:
            record_id = None
            reason = "Toxic, abusive, or threatening content detected in user prompt."
            if persist_log:
                record_id = self._insert_log(
                    validation_type="input",
                    risk_category="Toxicity",
                    severity="High",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=toxic_matches,
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Toxicity",
                severity="High",
                reason=reason,
                detected_issues=toxic_matches,
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 7. Threat Generation & Intimidation Detection
        is_threat_gen, threat_pattern = ThreatGenerationValidator.detect(text)
        if is_threat_gen:
            record_id = None
            reason = "Request to generate threatening or intimidating content."
            detected_issues = ["Request to generate threatening or intimidating content."]
            if threat_pattern:
                detected_issues.append(f"Matched pattern: '{threat_pattern}'")
            if persist_log:
                record_id = self._insert_log(
                    validation_type="input",
                    risk_category="Threat Generation / Harmful Content",
                    severity="High",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=detected_issues,
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Threat Generation / Harmful Content",
                severity="High",
                reason=reason,
                detected_issues=detected_issues,
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 8. Credential Exposure in prompt (Prevent user from accidentally sending secrets)
        for name, pattern in SensitiveDataValidator.API_KEY_PATTERNS:
            match = pattern.search(text)
            if match:
                record_id = None
                reason = f"Security hazard: Sensitive credential ({name}) detected in prompt."
                if persist_log:
                    record_id = self._insert_log(
                        validation_type="input",
                        risk_category="Secret Exposure",
                        severity="High",
                        action="BLOCK",
                        validation_reason=reason,
                        detected_issues=[name],
                        raw_text="[REDACTED PROMPT CONTAINING SECRET]",
                        status_val="failed",
                    )
                return GuardrailsCheckResponse(
                    validation_status="failed",
                    action="BLOCK",
                    risk_category="Secret Exposure",
                    severity="High",
                    reason=reason,
                    detected_issues=[name],
                    record_id=record_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        # Passed all input checks
        record_id = None
        reason = "Input successfully verified against prompt injection, jailbreak, and toxicity guardrails."
        if persist_log:
            record_id = self._insert_log(
                validation_type="input",
                risk_category="None",
                severity="None",
                action="ALLOW",
                validation_reason=reason,
                detected_issues=[],
                raw_text=text,
                status_val="passed",
            )

        return GuardrailsCheckResponse(
            validation_status="passed",
            action="ALLOW",
            risk_category="None",
            severity="None",
            reason=reason,
            detected_issues=[],
            record_id=record_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # -------------------------------------------------------------------------
    # Output Validation
    # -------------------------------------------------------------------------

    def validate_output(self, text: Optional[str], persist_log: bool = True) -> GuardrailsCheckResponse:
        """Evaluate an AI generated response before returning to client.

        Performs toxicity, harmful content, secret leakage, and sensitive PII redaction checks.
        """
        if text is None:
            text = ""

        # 1. Guardrails AI Official Engine Validation (Toxicity)
        if self._output_guard is not None and text:
            try:
                outcome = self._output_guard.validate(text)
                if not outcome.validation_passed:
                    summaries = getattr(outcome, "validation_summaries", [])
                    detected = [getattr(s, "validator_name", "Validator") for s in summaries]
                    # If toxicity detected by Guardrails AI, block immediately
                    if any("Toxicity" in d for d in detected):
                        reasons = [getattr(s, "failure_reason", "") for s in summaries if "Toxicity" in getattr(s, "validator_name", "")]
                        reason = "; ".join(reasons) or "Generated response blocked by Guardrails AI: Toxic or harmful content detected."
                        record_id = None
                        if persist_log:
                            record_id = self._insert_log(
                                validation_type="output",
                                risk_category="Toxicity",
                                severity="High",
                                action="BLOCK",
                                validation_reason=reason,
                                detected_issues=detected,
                                raw_text=text,
                                status_val="failed",
                            )
                        return GuardrailsCheckResponse(
                            validation_status="failed",
                            action="BLOCK",
                            risk_category="Toxicity",
                            severity="High",
                            reason=reason,
                            detected_issues=detected,
                            record_id=record_id,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
            except Exception as e:
                # Fail-safe principle: Never silently bypass on internal error
                record_id = None
                reason = f"Fail-safe block: Output verification encountered an internal error ({str(e)})."
                if persist_log:
                    record_id = self._insert_log(
                        validation_type="output",
                        risk_category="System Error",
                        severity="High",
                        action="BLOCK",
                        validation_reason=reason,
                        detected_issues=["guardrails_engine_error"],
                        raw_text=text,
                        status_val="failed",
                    )
                return GuardrailsCheckResponse(
                    validation_status="failed",
                    action="BLOCK",
                    risk_category="System Error",
                    severity="High",
                    reason=reason,
                    detected_issues=["guardrails_engine_error"],
                    record_id=record_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        # 2. Secondary Toxicity Check
        toxic_matches = []
        for pattern in ToxicityValidator.TOXICITY_PATTERNS:
            match = pattern.search(text)
            if match:
                toxic_matches.append(match.group(0))

        if toxic_matches:
            record_id = None
            reason = "Generated response contains toxic, abusive, or threatening language."
            if persist_log:
                record_id = self._insert_log(
                    validation_type="output",
                    risk_category="Toxicity",
                    severity="High",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=toxic_matches,
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Toxicity",
                severity="High",
                reason=reason,
                detected_issues=toxic_matches,
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 2. Harmful content (malware, weapons, bomb synthesis, illicit activities)
        harmful_patterns = [
            re.compile(r"(?i)\b(instructions\s+to\s+(build|make|assemble|create)\s+(a\s+)?(pipe\s+)?bomb|how\s+to\s+(build|make|assemble|create)\s+(a\s+)?(pipe\s+)?bomb)\b"),
            re.compile(r"(?i)\b(how\s+to\s+create\s+ransomware|exploit\s+code\s+to\s+ddos|script\s+to\s+steal\s+passwords)\b"),
            re.compile(r"(?i)\b(manufacture\s+(methamphetamine|heroin|fentanyl|ricin|sarin))\b"),
            re.compile(r"(?i)\b(how\s+to\s+(hack|infiltrate)\s+into\s+a\s+bank\s+system)\b"),
        ]
        harmful_matches = []
        for pattern in harmful_patterns:
            match = pattern.search(text)
            if match:
                harmful_matches.append(match.group(0))

        if harmful_matches:
            record_id = None
            reason = "Generated response contains dangerous or hazardous material violating safety policies."
            if persist_log:
                record_id = self._insert_log(
                    validation_type="output",
                    risk_category="Harmful Content",
                    severity="Critical",
                    action="BLOCK",
                    validation_reason=reason,
                    detected_issues=harmful_matches,
                    raw_text=text,
                    status_val="failed",
                )
            return GuardrailsCheckResponse(
                validation_status="failed",
                action="BLOCK",
                risk_category="Harmful Content",
                severity="Critical",
                reason=reason,
                detected_issues=harmful_matches,
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 3. Hidden System Prompt Disclosure
        prompt_leak_patterns = [
            re.compile(r"(?i)\b(here\s+is\s+my\s+(full\s+)?system\s+prompt|my\s+exact\s+system\s+instructions\s+are)\b"),
            re.compile(r"(?i)\b(my\s+initial\s+developer\s+prompt\s+states\s*:)\b"),
        ]
        for pattern in prompt_leak_patterns:
            match = pattern.search(text)
            if match:
                record_id = None
                reason = "Generated response attempted to disclose confidential internal system prompts."
                if persist_log:
                    record_id = self._insert_log(
                        validation_type="output",
                        risk_category="Prompt Leakage",
                        severity="High",
                        action="BLOCK",
                        validation_reason=reason,
                        detected_issues=[match.group(0)],
                        raw_text=text,
                        status_val="failed",
                    )
                return GuardrailsCheckResponse(
                    validation_status="failed",
                    action="BLOCK",
                    risk_category="Prompt Leakage",
                    severity="High",
                    reason=reason,
                    detected_issues=[match.group(0)],
                    record_id=record_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        # 4. Credential / Secret Redaction
        sanitized_text = text
        detected_secrets = []
        for name, pattern in SensitiveDataValidator.API_KEY_PATTERNS:
            if pattern.search(sanitized_text):
                detected_secrets.append(name)
                sanitized_text = pattern.sub("[REDACTED_API_KEY]", sanitized_text)

        # 5. Sensitive Personal Identifiable Information (PII) Redaction
        detected_pii = []
        # SSN
        ssn_pat = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        if ssn_pat.search(sanitized_text):
            detected_pii.append("Social Security Number")
            sanitized_text = ssn_pat.sub("[REDACTED_SSN]", sanitized_text)

        # Credit Card
        cc_pat = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
        if cc_pat.search(sanitized_text):
            detected_pii.append("Credit Card")
            sanitized_text = cc_pat.sub("[REDACTED_CREDIT_CARD]", sanitized_text)

        # Email
        email_pat = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        if email_pat.search(sanitized_text):
            detected_pii.append("Email Address")
            sanitized_text = email_pat.sub("[REDACTED_EMAIL]", sanitized_text)

        # Phone Number
        phone_pat = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
        if phone_pat.search(sanitized_text):
            detected_pii.append("Phone Number")
            sanitized_text = phone_pat.sub("[REDACTED_PHONE]", sanitized_text)

        # If redactions were made:
        if detected_secrets or detected_pii:
            all_detected = detected_secrets + detected_pii
            risk_cat = "Secret Exposure" if detected_secrets else "Sensitive PII"
            severity = "High" if detected_secrets else "Medium"
            reason = f"Sensitive content detected and sanitized via redaction ({', '.join(all_detected)})."

            record_id = None
            if persist_log:
                record_id = self._insert_log(
                    validation_type="output",
                    risk_category=risk_cat,
                    severity=severity,
                    action="REDACT",
                    validation_reason=reason,
                    detected_issues=all_detected,
                    raw_text=sanitized_text,
                    status_val="redacted",
                )

            return GuardrailsCheckResponse(
                validation_status="passed",
                action="REDACT",
                risk_category=risk_cat,
                severity=severity,
                reason=reason,
                detected_issues=all_detected,
                sanitized_text=sanitized_text,
                record_id=record_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # 6. All Output checks passed cleanly
        record_id = None
        reason = "Generated response successfully passed output safety and compliance moderation."
        if persist_log:
            record_id = self._insert_log(
                validation_type="output",
                risk_category="None",
                severity="None",
                action="ALLOW",
                validation_reason=reason,
                detected_issues=[],
                raw_text=text,
                status_val="passed",
            )

        return GuardrailsCheckResponse(
            validation_status="passed",
            action="ALLOW",
            risk_category="None",
            severity="None",
            reason=reason,
            detected_issues=[],
            sanitized_text=text,
            record_id=record_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # -------------------------------------------------------------------------
    # History & Aggregated Summaries
    # -------------------------------------------------------------------------

    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        action_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> GuardrailsHistoryResponse:
        """Fetch chronological safety logs with optional action/type filtering."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                conditions = []
                params: List[Any] = []

                if action_filter:
                    conditions.append("action = ?")
                    params.append(action_filter.upper())
                if type_filter:
                    conditions.append("validation_type = ?")
                    params.append(type_filter.lower())

                where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

                count_query = f"SELECT COUNT(*) FROM safety_logs {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]

                data_query = f"""
                    SELECT id, timestamp, validation_type, risk_category,
                           severity, action, validation_reason, detected_issues,
                           input_snippet, status
                    FROM safety_logs
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """
                cursor.execute(data_query, params + [limit, offset])
                rows = cursor.fetchall()

                logs = []
                for row in rows:
                    issues = []
                    try:
                        issues = json.loads(row["detected_issues"])
                    except Exception:
                        pass

                    logs.append(
                        GuardrailsLogItem(
                            id=row["id"],
                            timestamp=row["timestamp"],
                            validation_type=row["validation_type"],
                            risk_category=row["risk_category"],
                            severity=row["severity"],
                            action=row["action"],
                            validation_reason=row["validation_reason"],
                            detected_issues=issues,
                            input_snippet=row["input_snippet"],
                            status=row["status"],
                        )
                    )

                return GuardrailsHistoryResponse(total=total, logs=logs)

    def get_summary(self) -> GuardrailsSummaryResponse:
        """Compute real aggregate statistics from stored safety logs."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM safety_logs")
                total_checked = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM safety_logs WHERE action = 'ALLOW'")
                accepted_requests = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM safety_logs WHERE action = 'BLOCK'")
                blocked_requests = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM safety_logs WHERE action = 'FLAG'")
                flagged_requests = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM safety_logs WHERE action = 'REDACT'")
                redacted_requests = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM safety_logs WHERE risk_category = 'Prompt Injection'")
                injection_detections = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM safety_logs WHERE risk_category IN ('Toxicity', 'Threat Generation / Harmful Content')"
                )
                toxicity_detections = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM safety_logs WHERE validation_type = 'output' AND action = 'BLOCK'"
                )
                unsafe_output_detections = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM safety_logs WHERE risk_category = 'Jailbreak'")
                jailbreak_detections = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM safety_logs WHERE risk_category IN ('Sensitive PII', 'Secret Exposure')"
                )
                sensitive_data_detections = cursor.fetchone()[0]

                return GuardrailsSummaryResponse(
                    total_checked=total_checked,
                    accepted_requests=accepted_requests,
                    blocked_requests=blocked_requests,
                    flagged_requests=flagged_requests,
                    redacted_requests=redacted_requests,
                    injection_detections=injection_detections,
                    toxicity_detections=toxicity_detections,
                    unsafe_output_detections=unsafe_output_detections,
                    jailbreak_detections=jailbreak_detections,
                    sensitive_data_detections=sensitive_data_detections,
                    status="operational",
                )

    def clear_logs(self) -> None:
        """Clear all safety records (used in test setup/teardown)."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM safety_logs")
                conn.commit()


# Singleton Instance
guardrails_service = GuardrailsService()
