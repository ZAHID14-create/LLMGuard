import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from app.core.config import settings
    from app.models.schemas import (
        SystemReportSummary,
        ReportExportResponse,
    )
    from app.services.system_service import SystemService
    from app.services.llm_service import llm_service
    from app.services.evaluation_service import evaluation_service
    from app.services.guardrails_service import guardrails_service
    from app.services.observability_service import observability_service
except ImportError:
    from backend.app.core.config import settings
    from backend.app.models.schemas import (
        SystemReportSummary,
        ReportExportResponse,
    )
    from backend.app.services.system_service import SystemService
    from backend.app.services.llm_service import llm_service
    from backend.app.services.evaluation_service import evaluation_service
    from backend.app.services.guardrails_service import guardrails_service
    from backend.app.services.observability_service import observability_service


class ReportsService:
    """Service providing unified cross-module reporting, compliance audit summaries,

    and multi-format export capabilities (JSON, Markdown, CSV).
    """

    def get_summary(self) -> SystemReportSummary:
        """Aggregate real-time metrics across all active platform subsystems."""
        now_ts = datetime.now(timezone.utc).isoformat()
        return SystemReportSummary(
            generated_at=now_ts,
            app_name=settings.PROJECT_NAME,
            app_version=settings.API_VERSION,
            environment=settings.ENVIRONMENT,
            current_phase="Phase 8: Live API Configuration, Integration Testing & Final Demonstration",
            llm_metrics=llm_service.get_metrics(),
            evaluation_summary=evaluation_service.get_summary(),
            guardrails_summary=guardrails_service.get_summary(),
            observability_summary=observability_service.get_summary(),
        )

    def export_report(self, report_type: str = "system", export_format: str = "markdown") -> ReportExportResponse:
        """Export system, evaluation, safety, or observability audit reports."""
        clean_type = report_type.lower()
        clean_format = export_format.lower()
        now_dt = datetime.now(timezone.utc)
        iso_now = now_dt.isoformat()
        date_str = now_dt.strftime("%Y%m%d_%H%M%S")

        if clean_type == "evaluation":
            content, filename = self._generate_evaluation_report(clean_format, date_str, iso_now)
        elif clean_type == "safety":
            content, filename = self._generate_safety_report(clean_format, date_str, iso_now)
        elif clean_type == "observability":
            content, filename = self._generate_observability_report(clean_format, date_str, iso_now)
        else:
            clean_type = "system"
            content, filename = self._generate_system_report(clean_format, date_str, iso_now)

        return ReportExportResponse(
            report_type=clean_type,
            format=clean_format,
            filename=filename,
            generated_at=iso_now,
            content=content,
        )

    def _generate_system_report(self, fmt: str, date_str: str, iso_now: str) -> tuple[str, str]:
        summary = self.get_summary()

        if fmt == "json":
            filename = f"llmguard_system_report_{date_str}.json"
            return summary.model_dump_json(indent=2), filename

        if fmt == "csv":
            filename = f"llmguard_system_report_{date_str}.csv"
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["subsystem", "metric", "value", "status"])
            writer.writerow(["LLM Inference", "total_requests", summary.llm_metrics.total_requests, "operational"])
            writer.writerow(["LLM Inference", "simulated_requests", summary.llm_metrics.simulated_requests, "simulation_mode"])
            writer.writerow(["LLM Inference", "average_latency_ms", summary.llm_metrics.average_latency_ms, "measured"])
            writer.writerow(["LLM Evaluation", "faithfulness_score", summary.evaluation_summary.average_faithfulness, summary.evaluation_summary.status])
            writer.writerow(["LLM Evaluation", "relevancy_score", summary.evaluation_summary.average_answer_relevancy, summary.evaluation_summary.status])
            writer.writerow(["LLM Evaluation", "hallucination_score", summary.evaluation_summary.average_hallucination_score, "factual_agreement"])
            writer.writerow(["Safety Guardrails", "total_checked", summary.guardrails_summary.total_checked, "active"])
            writer.writerow(["Safety Guardrails", "blocked_requests", summary.guardrails_summary.blocked_requests, "intercepted"])
            writer.writerow(["Safety Guardrails", "redacted_requests", summary.guardrails_summary.redacted_requests, "sanitized"])
            writer.writerow(["LLM Observability", "total_traces", summary.observability_summary.total_traces, "stored"])
            writer.writerow(["LLM Observability", "total_tokens", summary.observability_summary.total_tokens_consumed, "tracked"])
            writer.writerow(["LLM Observability", "connection_status", summary.observability_summary.connection_status, "telemetry_state"])
            return output.getvalue(), filename

        # Markdown Report
        filename = f"llmguard_system_report_{date_str}.md"
        md = f"""# LLMGuard – Unified Platform Audit & Telemetry Report

**Generated:** {iso_now}  
**Platform Version:** {summary.app_version}  
**Environment:** {summary.environment}  
**Status:** {summary.current_phase}  

---

## 1. Executive Summary & KPIs

| Subsystem | Primary Metric | Recorded Value | Status |
| :--- | :--- | :--- | :--- |
| **LLM Inference** | Total Requests | {summary.llm_metrics.total_requests} | Operational |
| **LLM Inference** | Average Latency | {summary.llm_metrics.average_latency_ms} ms | Measured |
| **LLM Evaluation** | Faithfulness Score | {(summary.evaluation_summary.average_faithfulness * 100):.1f}% | {summary.evaluation_summary.status} |
| **LLM Evaluation** | Relevancy Score | {(summary.evaluation_summary.average_answer_relevancy * 100):.1f}% | {summary.evaluation_summary.status} |
| **LLM Evaluation** | Hallucination Score | {(summary.evaluation_summary.average_hallucination_score * 100):.1f}% | (Factual Agreement) |
| **Safety Guardrails**| Prompts Inspected | {summary.guardrails_summary.total_checked} | Active |
| **Safety Guardrails**| Threats Blocked | {summary.guardrails_summary.blocked_requests} | Intercepted |
| **Safety Guardrails**| PII/Secrets Redacted| {summary.guardrails_summary.redacted_requests} | Sanitized |
| **LLM Observability**| Total Traces Captured| {summary.observability_summary.total_traces} | Stored |
| **LLM Observability**| Total Tokens | {summary.observability_summary.total_tokens_consumed:,} | Tracked |
| **LLM Observability**| Langfuse Status | {summary.observability_summary.connection_status} | Telemetry State |

---

## 2. Subsystem Diagnostics

### A. Inference Engine (Google Gemini API)
- **Model:** `gemini-2.5-flash`
- **Total Requests Processed:** {summary.llm_metrics.total_requests}
- **Total Tokens Consumed:** {summary.llm_metrics.total_tokens:,}
- **Mean Roundtrip Latency:** {summary.llm_metrics.average_latency_ms} ms

### B. Evaluation Engine (DeepEval)
- **Total Test Cases Evaluated:** {summary.evaluation_summary.total_evaluations}
- **Passed Evaluations:** {summary.evaluation_summary.successful_evaluations}
- **Failed Evaluations:** {summary.evaluation_summary.failed_evaluations}
- **Evaluation Thresholds:** Faithfulness (≥ {settings.FAITHFULNESS_THRESHOLD}), Relevancy (≥ {settings.ANSWER_RELEVANCY_THRESHOLD}), Hallucination (≥ {settings.HALLUCINATION_THRESHOLD})

### C. Safety Guardrails (Guardrails AI)
- **Prompt Injections Intercepted:** {summary.guardrails_summary.injection_detections}
- **Jailbreak Personas Intercepted:** {summary.guardrails_summary.jailbreak_detections}
- **Toxic Content Filtered:** {summary.guardrails_summary.toxicity_detections}
- **Sensitive Data & API Key Protections:** {summary.guardrails_summary.sensitive_data_detections}
- **Audit Persistence:** Local SQLite database at `backend/data/safety_logs.db`

### D. Observability & Telemetry (Langfuse)
- **Connection Status:** {summary.observability_summary.connection_status}
- **Input Prompt Tokens:** {summary.observability_summary.total_input_tokens:,}
- **Output Completion Tokens:** {summary.observability_summary.total_output_tokens:,}
- **Audit Mode:** Hybrid (Remote streaming when configured + Local SQLite trace fallback)

---
*Report generated by LLMGuard Core Telemetry Engine.*
"""
        return md, filename

    def _generate_evaluation_report(self, fmt: str, date_str: str, iso_now: str) -> tuple[str, str]:
        summary = evaluation_service.get_summary()
        history = evaluation_service.get_history(limit=100)

        if fmt == "json":
            filename = f"llmguard_evaluation_report_{date_str}.json"
            data = {
                "generated_at": iso_now,
                "summary": summary.model_dump(),
                "history": [r.model_dump() for r in history],
            }
            return json.dumps(data, indent=2), filename

        if fmt == "csv":
            filename = f"llmguard_evaluation_history_{date_str}.csv"
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "evaluation_id", "timestamp", "category", "evaluation_status",
                "faithfulness_score", "answer_relevancy_score", "hallucination_score",
                "hallucination_risk", "question", "actual_response"
            ])
            for r in history:
                writer.writerow([
                    r.evaluation_id,
                    r.timestamp,
                    r.category,
                    r.evaluation_status,
                    r.faithfulness_score,
                    r.answer_relevancy_score,
                    r.hallucination_score,
                    r.hallucination_risk,
                    r.question.replace("\n", " ")[:150],
                    r.actual_response.replace("\n", " ")[:150],
                ])
            return output.getvalue(), filename

        # Markdown Report
        filename = f"llmguard_evaluation_report_{date_str}.md"
        md = f"""# LLMGuard – DeepEval LLM Evaluation Report

**Generated:** {iso_now}  
**Evaluator Model:** {settings.EVALUATION_MODEL}  
**Judge Adapter:** Custom Google GenAI DeepEval Model Adapter  

---

## Metric Definitions & Benchmark Standards
1. **Faithfulness (Pass Threshold: ≥ {settings.FAITHFULNESS_THRESHOLD}):** Measures whether factual claims in the generated answer are grounded in and directly supported by reference context.
2. **Answer Relevancy (Pass Threshold: ≥ {settings.ANSWER_RELEVANCY_THRESHOLD}):** Measures how directly and concisely the answer addresses the user prompt without irrelevant deviation.
3. **Hallucination Score vs Risk:**
   - **Hallucination Score (Agreement Rate, Pass: ≥ {settings.HALLUCINATION_THRESHOLD}):** 1.0 indicates zero hallucination (complete factual agreement with context).
   - **Hallucination Risk (1.0 - Agreement Rate):** Probability of fabricated or ungrounded assertions.

## Aggregate Evaluation Performance
- **Total Evaluations:** {summary.total_evaluations}
- **Average Faithfulness:** {(summary.average_faithfulness * 100):.1f}%
- **Average Answer Relevancy:** {(summary.average_answer_relevancy * 100):.1f}%
- **Average Hallucination Score (Agreement):** {(summary.average_hallucination_score * 100):.1f}%
- **Average Hallucination Risk:** {(summary.average_hallucination_risk * 100):.1f}%
- **Passed Test Cases:** {summary.successful_evaluations}
- **Failed Test Cases:** {summary.failed_evaluations}
- **API Status:** {summary.status}

## Recent Evaluation Cases ({len(history)} recorded)
| ID | Status | Category | Faithfulness | Relevancy | Hallucination Score | Risk |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
"""
        if not history:
            md += "| - | Empty | No evaluations recorded yet | - | - | - | - |\n"
        else:
            for r in history[:20]:
                f_str = f"{(r.faithfulness_score * 100):.0f}%" if r.faithfulness_score is not None else "N/A"
                rel_str = f"{(r.answer_relevancy_score * 100):.0f}%" if r.answer_relevancy_score is not None else "N/A"
                h_str = f"{(r.hallucination_score * 100):.0f}%" if r.hallucination_score is not None else "N/A"
                risk_str = f"{(r.hallucination_risk * 100):.0f}%" if r.hallucination_risk is not None else "N/A"
                md += f"| {r.evaluation_id} | {r.evaluation_status} | {r.category} | {f_str} | {rel_str} | {h_str} | {risk_str} |\n"

        return md, filename

    def _generate_safety_report(self, fmt: str, date_str: str, iso_now: str) -> tuple[str, str]:
        summary = guardrails_service.get_summary()
        history = guardrails_service.get_history(limit=100)

        if fmt == "json":
            filename = f"llmguard_safety_report_{date_str}.json"
            data = {
                "generated_at": iso_now,
                "summary": summary.model_dump(),
                "logs": [log.model_dump() for log in history.logs],
            }
            return json.dumps(data, indent=2), filename

        if fmt == "csv":
            filename = f"llmguard_safety_audit_logs_{date_str}.csv"
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "record_id", "timestamp", "validation_type", "risk_category",
                "severity", "action", "status", "validation_reason", "input_snippet"
            ])
            for log in history.logs:
                writer.writerow([
                    log.id,
                    log.timestamp,
                    log.validation_type,
                    log.risk_category,
                    log.severity,
                    log.action,
                    log.status,
                    log.validation_reason.replace("\n", " "),
                    log.input_snippet.replace("\n", " "),
                ])
            return output.getvalue(), filename

        # Markdown Report
        filename = f"llmguard_safety_report_{date_str}.md"
        md = f"""# LLMGuard – Guardrails AI Safety & Security Audit Report

**Generated:** {iso_now}  
**Framework:** Guardrails AI with bidirectional inspection  
**Audit Storage:** Persistent SQLite Database (`backend/data/safety_logs.db`)  

---

## Safety Threat Interception Metrics
- **Total Prompts & Responses Inspected:** {summary.total_checked}
- **Accepted (ALLOW):** {summary.accepted_requests}
- **Blocked (BLOCK):** {summary.blocked_requests}
- **Flagged / Warning (FLAG):** {summary.flagged_requests}
- **Sanitized & Redacted (REDACT):** {summary.redacted_requests}

### Breakdown by Threat Category
| Threat Category | Interceptions | Description |
| :--- | :---: | :--- |
| **Prompt Injections** | {summary.injection_detections} | System prompt reveal & instruction override attacks |
| **Jailbreak Exploits** | {summary.jailbreak_detections} | Persona exploits (DAN), filter bypass prompts |
| **Toxic / Hate Content** | {summary.toxicity_detections} | Harassment, abusive language, slurs |
| **Sensitive Data & API Keys** | {summary.sensitive_data_detections} | Exposed credentials, PII (SSN, credit cards, emails) |

> **Security Note:** Pattern and heuristic-based guardrails act as a critical defense-in-depth security barrier; they complement foundational model alignment and require continuous rule updates.

## Recent Audit Trail ({len(history.logs)} recorded)
| Record ID | Type | Action | Risk Category | Severity | Reason |
| :--- | :---: | :---: | :--- | :---: | :--- |
"""
        if not history.logs:
            md += "| - | - | - | No safety logs recorded yet | - | - |\n"
        else:
            for log in history.logs[:20]:
                md += f"| {log.id} | {log.validation_type} | {log.action} | {log.risk_category} | {log.severity} | {log.validation_reason[:60]}... |\n"

        return md, filename

    def _generate_observability_report(self, fmt: str, date_str: str, iso_now: str) -> tuple[str, str]:
        summary = observability_service.get_summary()
        history = observability_service.get_history(limit=100)

        if fmt == "json":
            filename = f"llmguard_observability_report_{date_str}.json"
            data = {
                "generated_at": iso_now,
                "summary": summary.model_dump(),
                "traces": [t.model_dump() for t in history.traces],
            }
            return json.dumps(data, indent=2), filename

        if fmt == "csv":
            filename = f"llmguard_observability_traces_{date_str}.csv"
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "trace_id", "timestamp", "name", "model", "latency_ms",
                "prompt_tokens", "completion_tokens", "total_tokens",
                "status", "error_type", "guardrail_status", "is_remote"
            ])
            for t in history.traces:
                writer.writerow([
                    t.trace_id,
                    t.timestamp,
                    t.name,
                    t.model or "",
                    t.latency_ms,
                    t.prompt_tokens or "",
                    t.completion_tokens or "",
                    t.total_tokens or "",
                    t.status,
                    t.error_type or "",
                    t.guardrail_status or "",
                    t.is_remote,
                ])
            return output.getvalue(), filename

        # Markdown Report
        filename = f"llmguard_observability_report_{date_str}.md"
        md = f"""# LLMGuard – Langfuse LLM Observability & Telemetry Report

**Generated:** {iso_now}  
**Observability Engine:** Langfuse SDK (v5.2+)  
**Telemetry Mode:** Hybrid (Remote streaming when configured + Local SQLite audit records)  

---

## Key Telemetry Metrics
- **Total Recorded Traces:** {summary.total_traces}
- **Successful Requests:** {summary.successful_requests}
- **Failed / Blocked Requests:** {summary.failed_requests}
- **Average Roundtrip Latency:** {summary.average_latency_ms} ms
- **Input Prompt Tokens:** {summary.total_input_tokens:,}
- **Output Completion Tokens:** {summary.total_output_tokens:,}
- **Total Tokens Consumed:** {summary.total_tokens_consumed:,}
- **Langfuse Cloud Synced Traces:** {getattr(summary, 'cloud_synced_traces', 0)}
- **Local SQLite Audit Records:** {getattr(summary, 'local_only_traces', 0)}
- **Langfuse Cloud Connection:** {summary.connection_status}

## Recent Execution Traces ({len(history.traces)} recorded)
| Trace ID | Operation | Model | Latency | Tokens (In/Out/Total) | Status | Storage |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
"""
        if not history.traces:
            md += "| - | - | - | - | No execution traces recorded yet | - | - |\n"
        else:
            for t in history.traces[:20]:
                tokens_str = f"{t.prompt_tokens or 0}/{t.completion_tokens or 0}/{t.total_tokens or 0}"
                storage = "Langfuse Cloud" if t.is_remote else "Local SQLite"
                md += f"| {t.trace_id[:16]}... | {t.name} | {t.model or '–'} | {t.latency_ms:.1f}ms | {tokens_str} | {t.status} | {storage} |\n"

        return md, filename


# Singleton instance
reports_service = ReportsService()
