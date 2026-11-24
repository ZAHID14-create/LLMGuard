"""Automated Unit & Integration Tests for Reports & Cross-Module Integration (Phase 6)."""

import json
import pytest

try:
    from app.services.reports_service import reports_service, ReportsService
    from app.models.schemas import SystemReportSummary, ReportExportResponse
    from app.api.endpoints import get_reports_summary, export_report
except ImportError:
    from backend.app.services.reports_service import reports_service, ReportsService
    from backend.app.models.schemas import SystemReportSummary, ReportExportResponse
    from backend.app.api.endpoints import get_reports_summary, export_report


def test_reports_summary_generation():
    """Test 1: Verify get_summary aggregates all subsystems into SystemReportSummary."""
    summary = reports_service.get_summary()
    assert isinstance(summary, SystemReportSummary)
    assert summary.app_name == "LLMGuard – AI Evaluation & Safety Monitoring Platform"
    assert summary.app_version == "0.8.0"
    assert "Phase 8" in summary.current_phase
    assert summary.llm_metrics is not None
    assert summary.evaluation_summary is not None
    assert summary.guardrails_summary is not None
    assert summary.observability_summary is not None


def test_reports_export_system_markdown():
    """Test 2: Verify exporting system report as Markdown."""
    res = reports_service.export_report(report_type="system", export_format="markdown")
    assert isinstance(res, ReportExportResponse)
    assert res.report_type == "system"
    assert res.format == "markdown"
    assert res.filename.endswith(".md")
    assert "# LLMGuard – Unified Platform Audit & Telemetry Report" in res.content
    assert "Inference Engine" in res.content
    assert "Safety Guardrails" in res.content


def test_reports_export_system_json():
    """Test 3: Verify exporting system report as JSON."""
    res = reports_service.export_report(report_type="system", export_format="json")
    assert isinstance(res, ReportExportResponse)
    assert res.format == "json"
    assert res.filename.endswith(".json")
    parsed = json.loads(res.content)
    assert parsed["app_version"] == "0.8.0"
    assert "llm_metrics" in parsed
    assert "guardrails_summary" in parsed


def test_reports_export_evaluation_markdown():
    """Test 4: Verify exporting DeepEval evaluation report as Markdown."""
    res = reports_service.export_report(report_type="evaluation", export_format="markdown")
    assert res.report_type == "evaluation"
    assert res.format == "markdown"
    assert "# LLMGuard – DeepEval LLM Evaluation Report" in res.content
    assert "Faithfulness" in res.content
    assert "Hallucination Score vs Risk" in res.content


def test_reports_export_evaluation_csv():
    """Test 5: Verify exporting evaluation history as CSV."""
    res = reports_service.export_report(report_type="evaluation", export_format="csv")
    assert res.format == "csv"
    assert res.filename.endswith(".csv")
    lines = res.content.strip().split("\n")
    assert len(lines) >= 1
    assert "evaluation_id" in lines[0]
    assert "faithfulness_score" in lines[0]


def test_reports_export_safety_markdown():
    """Test 6: Verify exporting safety guardrails report as Markdown."""
    res = reports_service.export_report(report_type="safety", export_format="markdown")
    assert res.report_type == "safety"
    assert res.format == "markdown"
    assert "# LLMGuard – Guardrails AI Safety & Security Audit Report" in res.content
    assert "Prompt Injections" in res.content
    assert "Jailbreak Exploits" in res.content


def test_reports_export_safety_csv():
    """Test 7: Verify exporting safety audit logs as CSV."""
    res = reports_service.export_report(report_type="safety", export_format="csv")
    assert res.format == "csv"
    assert res.filename.endswith(".csv")
    lines = res.content.strip().split("\n")
    assert "record_id" in lines[0]
    assert "validation_type" in lines[0]
    assert "risk_category" in lines[0]


def test_reports_export_observability_markdown():
    """Test 8: Verify exporting observability telemetry report as Markdown."""
    res = reports_service.export_report(report_type="observability", export_format="markdown")
    assert res.report_type == "observability"
    assert res.format == "markdown"
    assert "# LLMGuard – Langfuse LLM Observability & Telemetry Report" in res.content
    assert "Total Recorded Traces" in res.content
    assert "Average Roundtrip Latency" in res.content


def test_reports_export_observability_csv():
    """Test 9: Verify exporting observability traces as CSV."""
    res = reports_service.export_report(report_type="observability", export_format="csv")
    assert res.format == "csv"
    assert res.filename.endswith(".csv")
    lines = res.content.strip().split("\n")
    assert "trace_id" in lines[0]
    assert "latency_ms" in lines[0]


def test_reports_endpoints_direct():
    """Test 10: Verify FastAPI endpoint functions directly."""
    summary = get_reports_summary()
    assert isinstance(summary, SystemReportSummary)
    assert summary.app_version == "0.8.0"

    export_res = export_report(type="system", format="json")
    assert isinstance(export_res, ReportExportResponse)
    assert export_res.format == "json"


def test_reports_empty_database_handling():
    """Test 11: Verify reports generation succeeds without exceptions even with empty records."""
    custom_service = ReportsService()
    summary = custom_service.get_summary()
    assert summary is not None
    md, filename = custom_service._generate_evaluation_report("markdown", "test", "2026-11-23T00:00:00Z")
    assert bool(md) is True


def test_reports_export_system_csv():
    """Phase 7: Verify exporting unified system platform summary as CSV."""
    res = reports_service.export_report(report_type="system", export_format="csv")
    assert res.report_type == "system"
    assert res.format == "csv"
    assert res.filename.endswith(".csv")
    lines = res.content.strip().split("\n")
    assert "subsystem,metric,value,status" in lines[0]
    assert any("LLM Inference" in line for line in lines)
    assert any("Safety Guardrails" in line for line in lines)
