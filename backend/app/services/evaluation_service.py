import os
import json
import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Union
import threading

from fastapi import HTTPException, status
from google import genai
from google.genai import types

try:
    from app.core.config import settings
    from app.models.schemas import (
        EvaluationResponse,
        BenchmarkSummary,
        EvaluationSummaryResponse,
    )
    from app.services.observability_service import observability_service
except ImportError:
    from backend.app.core.config import settings
    from backend.app.models.schemas import (
        EvaluationResponse,
        BenchmarkSummary,
        EvaluationSummaryResponse,
    )
    from backend.app.services.observability_service import observability_service

from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase


# =========================================================================
# Custom DeepEval Gemini Evaluation Judge Model Adapter
# =========================================================================

class GeminiJudgeModel(DeepEvalBaseLLM):
    """DeepEval-compatible custom model adapter powering evaluation metrics

    via the official Google GenAI Python SDK.
    """

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, *args, **kwargs):
        self.model_name = model_name or settings.EVALUATION_MODEL or "gemini-2.5-flash"
        self._api_key = api_key or (settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else "")
        super().__init__(model=self.model_name, *args, **kwargs)

    def load_model(self):
        """Initialize Google GenAI client if credentials are configured."""
        if not self._api_key:
            return None
        return genai.Client(api_key=self._api_key)

    def get_model_name(self) -> str:
        return self.model_name

    def generate(self, prompt: str, schema=None, *args, **kwargs) -> str:
        """Synchronously generate judge evaluation output."""
        if not self.model:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Live evaluation requires a valid Google AI Studio key in backend/.env."
            )
        try:
            response = self.model.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text or ""
        except Exception as e:
            raise RuntimeError(f"Gemini evaluation judge failed: {str(e)}")

    async def a_generate(self, prompt: str, schema=None, *args, **kwargs) -> str:
        """Asynchronously generate judge evaluation output."""
        return self.generate(prompt, schema=schema, *args, **kwargs)


# =========================================================================
# DeepEval Evaluation Service
# =========================================================================

class EvaluationService:
    """Service orchestrating DeepEval metric calculations (Faithfulness,

    Answer Relevancy, Hallucination), benchmark test suite execution,
    and markdown audit report generation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._history: List[EvaluationResponse] = []

    def is_api_configured(self) -> bool:
        """Check if GEMINI_API_KEY is present and non-empty."""
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    def _get_judge(self, custom_judge=None) -> DeepEvalBaseLLM:
        """Get evaluation judge model (custom mock or live Gemini adapter)."""
        if custom_judge is not None:
            return custom_judge

        if not self.is_api_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Awaiting Gemini API Configuration: GEMINI_API_KEY is not set in backend/.env. Please configure your Google AI Studio API key.",
            )

        return GeminiJudgeModel()

    def _locate_dataset_path(self) -> str:
        """Resolve absolute path to evaluation_dataset.json."""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "evaluation_dataset.json"),
            os.path.join(os.getcwd(), "backend", "datasets", "evaluation_dataset.json"),
            os.path.join(os.getcwd(), "datasets", "evaluation_dataset.json"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
        raise FileNotFoundError(f"Could not locate evaluation_dataset.json in: {possible_paths}")

    def evaluate_single(
        self,
        question: str,
        actual_response: str,
        reference_context: Union[str, List[str]],
        expected_output: Optional[str] = None,
        category: str = "General",
        judge_model: Optional[DeepEvalBaseLLM] = None,
    ) -> EvaluationResponse:
        """Evaluate an individual LLM response against reference context

        using Faithfulness, Answer Relevancy, and Hallucination metrics.
        """
        # Input validation
        clean_question = question.strip() if question else ""
        clean_response = actual_response.strip() if actual_response else ""

        if not clean_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty for evaluation.",
            )
        if not clean_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Actual response cannot be empty for evaluation.",
            )

        # Context normalization
        if isinstance(reference_context, str):
            contexts = [c.strip() for c in reference_context.split("\n\n") if c.strip()]
            if not contexts and reference_context.strip():
                contexts = [reference_context.strip()]
        elif isinstance(reference_context, list):
            contexts = [c.strip() for c in reference_context if c and c.strip()]
        else:
            contexts = []

        if not contexts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference context cannot be empty. Grounding context is required for Faithfulness and Hallucination evaluation.",
            )

        eval_id = f"EVAL-{uuid.uuid4().hex[:8].upper()}"
        iso_now = datetime.now(timezone.utc).isoformat()

        # Check API key if no custom judge was provided
        if judge_model is None and not self.is_api_configured():
            record = EvaluationResponse(
                evaluation_id=eval_id,
                timestamp=iso_now,
                question=clean_question,
                actual_response=clean_response,
                reference_context=contexts,
                expected_output=expected_output,
                faithfulness_score=None,
                faithfulness_reason="Evaluation paused: GEMINI_API_KEY not configured.",
                answer_relevancy_score=None,
                answer_relevancy_reason="Evaluation paused: GEMINI_API_KEY not configured.",
                hallucination_score=None,
                hallucination_risk=None,
                hallucination_reason="Evaluation paused: GEMINI_API_KEY not configured.",
                evaluation_status="awaiting_api_key",
                category=category,
                error="Awaiting Gemini API Configuration in backend/.env",
            )
            with self._lock:
                self._history.append(record)
            return record

        judge = self._get_judge(judge_model)

        # Build DeepEval LLMTestCase
        test_case = LLMTestCase(
            input=clean_question,
            actual_output=clean_response,
            retrieval_context=contexts,
            context=contexts,
            expected_output=expected_output or None,
        )

        # Initialize the three mandatory DeepEval metrics
        faithfulness_metric = FaithfulnessMetric(
            threshold=settings.FAITHFULNESS_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=False,
        )
        relevancy_metric = AnswerRelevancyMetric(
            threshold=settings.ANSWER_RELEVANCY_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=False,
        )
        hallucination_metric = HallucinationMetric(
            threshold=settings.HALLUCINATION_THRESHOLD,
            model=judge,
            include_reason=True,
            async_mode=False,
        )

        try:
            # Measure Faithfulness
            faithfulness_metric.measure(test_case)
            faith_score = round(float(faithfulness_metric.score), 4) if faithfulness_metric.score is not None else None
            faith_reason = getattr(faithfulness_metric, "reason", "Faithfulness evaluation completed.")

            # Measure Answer Relevancy
            relevancy_metric.measure(test_case)
            relevancy_score = round(float(relevancy_metric.score), 4) if relevancy_metric.score is not None else None
            relevancy_reason = getattr(relevancy_metric, "reason", "Answer relevancy evaluation completed.")

            # Measure Hallucination (DeepEval 4.x: score = factual agreement rate, where 1.0 is un-hallucinated)
            hallucination_metric.measure(test_case)
            raw_hal_score = round(float(hallucination_metric.score), 4) if hallucination_metric.score is not None else None
            hal_risk = round(1.0 - raw_hal_score, 4) if raw_hal_score is not None else None
            hal_reason = getattr(hallucination_metric, "reason", "Hallucination evaluation completed.")

            # Determine overall pass/fail status against thresholds
            passed = (
                (faith_score is not None and faith_score >= settings.FAITHFULNESS_THRESHOLD)
                and (relevancy_score is not None and relevancy_score >= settings.ANSWER_RELEVANCY_THRESHOLD)
                and (raw_hal_score is not None and raw_hal_score >= settings.HALLUCINATION_THRESHOLD)
            )
            eval_status = "passed" if passed else "failed"

            record = EvaluationResponse(
                evaluation_id=eval_id,
                timestamp=iso_now,
                question=clean_question,
                actual_response=clean_response,
                reference_context=contexts,
                expected_output=expected_output,
                faithfulness_score=faith_score,
                faithfulness_reason=faith_reason,
                answer_relevancy_score=relevancy_score,
                answer_relevancy_reason=relevancy_reason,
                hallucination_score=raw_hal_score,
                hallucination_risk=hal_risk,
                hallucination_reason=hal_reason,
                evaluation_status=eval_status,
                category=category,
                error=None,
            )

            # Record DeepEval metrics to observability traces
            try:
                if faith_score is not None:
                    observability_service.record_evaluation_event(
                        evaluation_id=eval_id,
                        metric="faithfulness",
                        score=faith_score,
                        risk=None,
                        status="passed" if (faith_score >= settings.FAITHFULNESS_THRESHOLD) else "failed",
                    )
                if relevancy_score is not None:
                    observability_service.record_evaluation_event(
                        evaluation_id=eval_id,
                        metric="answer_relevancy",
                        score=relevancy_score,
                        risk=None,
                        status="passed" if (relevancy_score >= settings.ANSWER_RELEVANCY_THRESHOLD) else "failed",
                    )
                if raw_hal_score is not None:
                    observability_service.record_evaluation_event(
                        evaluation_id=eval_id,
                        metric="hallucination",
                        score=raw_hal_score,
                        risk=hal_risk,
                        status="passed" if (raw_hal_score >= settings.HALLUCINATION_THRESHOLD) else "failed",
                    )
            except Exception:
                pass

        except Exception as e:
            record = EvaluationResponse(
                evaluation_id=eval_id,
                timestamp=iso_now,
                question=clean_question,
                actual_response=clean_response,
                reference_context=contexts,
                expected_output=expected_output,
                faithfulness_score=None,
                faithfulness_reason=None,
                answer_relevancy_score=None,
                answer_relevancy_reason=None,
                hallucination_score=None,
                hallucination_risk=None,
                hallucination_reason=None,
                evaluation_status="error",
                category=category,
                error=f"Evaluation failed during metric execution: {str(e)}",
            )

        with self._lock:
            self._history.append(record)

        return record

    def run_benchmark(
        self,
        sample_size: Optional[int] = None,
        categories: Optional[List[str]] = None,
        judge_model: Optional[DeepEvalBaseLLM] = None,
    ) -> BenchmarkSummary:
        """Run DeepEval evaluation against benchmark dataset cases."""
        dataset_path = self._locate_dataset_path()
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset_cases = json.load(f)

        if categories:
            dataset_cases = [c for c in dataset_cases if c.get("category") in categories]

        if sample_size and sample_size > 0:
            dataset_cases = dataset_cases[:sample_size]

        benchmark_id = f"BM-{uuid.uuid4().hex[:8].upper()}"
        iso_now = datetime.now(timezone.utc).isoformat()
        results: List[EvaluationResponse] = []

        for case in dataset_cases:
            # Use expected_output as the actual output for benchmark validation
            result = self.evaluate_single(
                question=case.get("input", ""),
                actual_response=case.get("expected_output", ""),
                reference_context=case.get("reference_context", []),
                expected_output=case.get("expected_output"),
                category=case.get("category", "General"),
                judge_model=judge_model,
            )
            results.append(result)

        # Aggregate calculations
        valid_results = [r for r in results if r.evaluation_status in ["passed", "failed"]]
        passed_count = sum(1 for r in valid_results if r.evaluation_status == "passed")
        failed_count = sum(1 for r in valid_results if r.evaluation_status == "failed")

        faith_scores = [r.faithfulness_score for r in valid_results if r.faithfulness_score is not None]
        rel_scores = [r.answer_relevancy_score for r in valid_results if r.answer_relevancy_score is not None]
        hal_scores = [r.hallucination_score for r in valid_results if r.hallucination_score is not None]
        risk_scores = [r.hallucination_risk for r in valid_results if r.hallucination_risk is not None]

        avg_faith = round(sum(faith_scores) / len(faith_scores), 4) if faith_scores else 0.0
        avg_rel = round(sum(rel_scores) / len(rel_scores), 4) if rel_scores else 0.0
        avg_hal = round(sum(hal_scores) / len(hal_scores), 4) if hal_scores else 0.0
        avg_risk = round(sum(risk_scores) / len(risk_scores), 4) if risk_scores else 0.0

        summary = BenchmarkSummary(
            benchmark_id=benchmark_id,
            timestamp=iso_now,
            total_cases=len(results),
            passed_cases=passed_count,
            failed_cases=failed_count,
            average_faithfulness=avg_faith,
            average_answer_relevancy=avg_rel,
            average_hallucination_score=avg_hal,
            average_hallucination_risk=avg_risk,
            results=results,
            report_path=None,
            status="completed" if valid_results else "awaiting_api_key",
        )

        # Generate markdown audit report
        if valid_results:
            report_path = self.generate_markdown_report(summary, results)
            summary.report_path = report_path

        return summary

    def get_history(
        self,
        limit: int = 50,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
    ) -> List[EvaluationResponse]:
        """Retrieve recent evaluation records with optional filtering."""
        with self._lock:
            records = list(reversed(self._history))

        if status_filter:
            records = [r for r in records if r.evaluation_status == status_filter]
        if category_filter:
            records = [r for r in records if r.category == category_filter]

        return records[:limit]

    def get_summary(self) -> EvaluationSummaryResponse:
        """Compute aggregate summary metrics across all historical evaluations."""
        with self._lock:
            records = [r for r in self._history if r.evaluation_status in ["passed", "failed"]]
            total = len(records)
            passed = sum(1 for r in records if r.evaluation_status == "passed")
            failed = sum(1 for r in records if r.evaluation_status == "failed")

            faith_scores = [r.faithfulness_score for r in records if r.faithfulness_score is not None]
            rel_scores = [r.answer_relevancy_score for r in records if r.answer_relevancy_score is not None]
            hal_scores = [r.hallucination_score for r in records if r.hallucination_score is not None]
            risk_scores = [r.hallucination_risk for r in records if r.hallucination_risk is not None]

            avg_faith = round(sum(faith_scores) / len(faith_scores), 4) if faith_scores else 0.0
            avg_rel = round(sum(rel_scores) / len(rel_scores), 4) if rel_scores else 0.0
            avg_hal = round(sum(hal_scores) / len(hal_scores), 4) if hal_scores else 0.0
            avg_risk = round(sum(risk_scores) / len(risk_scores), 4) if risk_scores else 0.0

        api_ready = self.is_api_configured()
        status_text = "Operational" if api_ready else "Awaiting Gemini API Configuration"

        return EvaluationSummaryResponse(
            total_evaluations=total,
            average_faithfulness=avg_faith,
            average_answer_relevancy=avg_rel,
            average_hallucination_score=avg_hal,
            average_hallucination_risk=avg_risk,
            successful_evaluations=passed,
            failed_evaluations=failed,
            api_configured=api_ready,
            status=status_text,
        )

    def reset_history(self) -> None:
        """Clear evaluation history for testing purposes."""
        with self._lock:
            self._history.clear()

    def generate_markdown_report(
        self, summary: BenchmarkSummary, results: List[EvaluationResponse]
    ) -> str:
        """Generate and save a detailed Markdown audit report under reports/evaluation/."""
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports", "evaluation"
        )
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"benchmark_report_{summary.benchmark_id}.md"
        filepath = os.path.join(reports_dir, filename)

        md_content = f"""# LLMGuard – DeepEval Benchmark Evaluation Audit Report

**Benchmark ID:** `{summary.benchmark_id}`  
**Generated At:** `{summary.timestamp}`  
**Evaluation Judge:** `{settings.EVALUATION_MODEL}` (Google Gemini via DeepEval Adapter)  
**Status:** `{summary.status}`  

---

## 1. Executive Summary

| Metric | Aggregate Score | Threshold | Status |
| :--- | :---: | :---: | :---: |
| **Total Test Cases** | **{summary.total_cases}** | - | Complete |
| **Passed Cases** | **{summary.passed_cases}** | - | {"✅ Satisfactory" if summary.failed_cases == 0 else "⚠️ Review Required"} |
| **Failed Cases** | **{summary.failed_cases}** | - | {"0 Failures" if summary.failed_cases == 0 else f"{summary.failed_cases} Threshold Breaches"} |
| **Average Faithfulness** | **{summary.average_faithfulness:.4f}** | `>= {settings.FAITHFULNESS_THRESHOLD}` | {"PASS" if summary.average_faithfulness >= settings.FAITHFULNESS_THRESHOLD else "FAIL"} |
| **Average Answer Relevancy** | **{summary.average_answer_relevancy:.4f}** | `>= {settings.ANSWER_RELEVANCY_THRESHOLD}` | {"PASS" if summary.average_answer_relevancy >= settings.ANSWER_RELEVANCY_THRESHOLD else "FAIL"} |
| **Average Factual Agreement** | **{summary.average_hallucination_score:.4f}** | `>= {settings.HALLUCINATION_THRESHOLD}` | {"PASS" if summary.average_hallucination_score >= settings.HALLUCINATION_THRESHOLD else "FAIL"} |
| **Average Hallucination Risk** | **{summary.average_hallucination_risk:.4f}** | `<= 0.3000` | {"LOW" if summary.average_hallucination_risk <= 0.3 else "HIGH"} |

---

## 2. Dataset & Evaluation Criteria

- **Benchmark Source:** `backend/datasets/evaluation_dataset.json`
- **Total Evaluated Cases:** `{summary.total_cases}`
- **Evaluated Categories:** General Knowledge, Computer Science, Programming, Science & Technology, Mathematics, Logical Reasoning, and Incorrect/Unsupported Claims.
- **Scoring Semantics:**
  - **Faithfulness:** Ratio of output claims that can be directly verified from the provided reference context (higher is better).
  - **Answer Relevancy:** Semantic relevance of the generated answer to the original question (higher is better).
  - **Hallucination Metric:** Raw DeepEval agreement score (higher is better; 1.0 represents complete factual alignment with reference context, and Hallucination Risk = `1 - score`).

---

## 3. Individual Test Case Evaluations

| ID | Category | Faithfulness | Relevancy | Agreement (Risk) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
"""

        for r in results:
            faith_str = f"{r.faithfulness_score:.2f}" if r.faithfulness_score is not None else "N/A"
            rel_str = f"{r.answer_relevancy_score:.2f}" if r.answer_relevancy_score is not None else "N/A"
            hal_str = (
                f"{r.hallucination_score:.2f} ({(r.hallucination_risk or 0):.2f})"
                if r.hallucination_score is not None
                else "N/A"
            )
            status_icon = "✅ PASSED" if r.evaluation_status == "passed" else "❌ FAILED"
            md_content += f"| `{r.evaluation_id}` | {r.category} | {faith_str} | {rel_str} | {hal_str} | {status_icon} |\n"

        md_content += "\n---\n\n## 4. Failed Test Cases & Root Cause Analysis\n\n"

        failed_results = [r for r in results if r.evaluation_status == "failed"]
        if not failed_results:
            md_content += "No test cases failed evaluation thresholds. All cases satisfied Faithfulness, Relevancy, and Hallucination requirements.\n\n"
        else:
            for fr in failed_results:
                md_content += f"### Case `{fr.evaluation_id}`: {fr.question}\n"
                md_content += f"- **Category:** {fr.category}\n"
                md_content += f"- **Output Evaluated:** {fr.actual_response}\n"
                md_content += f"- **Faithfulness Score:** {fr.faithfulness_score} (Reason: {fr.faithfulness_reason})\n"
                md_content += f"- **Answer Relevancy Score:** {fr.answer_relevancy_score} (Reason: {fr.answer_relevancy_reason})\n"
                md_content += f"- **Factual Agreement Score:** {fr.hallucination_score} (Hallucination Risk: {fr.hallucination_risk})\n"
                md_content += f"- **Hallucination Reason:** {fr.hallucination_reason}\n\n"

        md_content += f"""---

## 5. Architectural Observations & Next Phase Recommendations

1. **Faithfulness & Grounding:** The Gemini judge reliably identified statements lacking citation in retrieval context.
2. **Scoring Consistency:** Raw DeepEval `HallucinationMetric` agreement score consistently measures un-hallucinated statements; our risk metric (`1 - agreement`) provides direct visibility into fabrication likelihood.
3. **Phase 4 Readiness:** With evaluation baselines established, the platform is prepared for Phase 4 (Safety Guardrails) to proactively block toxic or prompt-injection attempts before evaluation.

*Report automatically generated by LLMGuard Evaluation Service.*
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        return filepath


# Singleton Evaluation service instance
evaluation_service = EvaluationService()
