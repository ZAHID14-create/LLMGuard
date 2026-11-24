"""Automated test suite for DeepEval evaluation service, metrics, and benchmark runners."""

import os
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

try:
    from app.services.evaluation_service import (
        EvaluationService,
        GeminiJudgeModel,
    )
    from app.models.schemas import EvaluationResponse, BenchmarkSummary
    from app.core.config import settings
except ImportError:
    from backend.app.services.evaluation_service import (
        EvaluationService,
        GeminiJudgeModel,
    )
    from backend.app.models.schemas import EvaluationResponse, BenchmarkSummary
    from backend.app.core.config import settings

from deepeval.models.base_model import DeepEvalBaseLLM


class DummyJudgeModel(DeepEvalBaseLLM):
    """Mock DeepEval judge model returning deterministic answers for testing."""

    def __init__(self):
        super().__init__(model="mock-gemini-judge")

    def load_model(self):
        return self

    def get_model_name(self):
        return "mock-gemini-judge"

    def generate(self, prompt, schema=None, *args, **kwargs):
        return "YES. The statement is completely supported."

    async def a_generate(self, prompt, schema=None, *args, **kwargs):
        return self.generate(prompt, schema=schema, *args, **kwargs)


@pytest.fixture
def eval_service():
    service = EvaluationService()
    service.reset_history()
    return service


# =========================================================================
# 1. Faithfulness Metric Test
# =========================================================================
def test_faithfulness_metric_evaluation(eval_service):
    """1. Test successful faithfulness evaluation with mocked metric measure."""
    with patch("deepeval.metrics.FaithfulnessMetric.measure") as mock_faith, \
         patch("deepeval.metrics.AnswerRelevancyMetric.measure") as mock_rel, \
         patch("deepeval.metrics.HallucinationMetric.measure") as mock_hal:

        def mock_faith_impl(tc):
            tc_metric = mock_faith.__self__ if hasattr(mock_faith, "__self__") else None

        # Configure mock return values on instance
        with patch.object(settings, "GEMINI_API_KEY", "test-api-key"):
            judge = DummyJudgeModel()

            def measure_faith(tc):
                pass
            def measure_rel(tc):
                pass
            def measure_hal(tc):
                pass

            with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.measure", side_effect=measure_faith), \
                 patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.measure", side_effect=measure_rel), \
                 patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.measure", side_effect=measure_hal):

                with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.score", 0.95), \
                     patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.reason", "100% of claims supported by context."), \
                     patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.score", 0.90), \
                     patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.reason", "Directly answers question."), \
                     patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.score", 0.88), \
                     patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.reason", "Factual agreement confirmed."):

                    res = eval_service.evaluate_single(
                        question="What is Canberra?",
                        actual_response="Canberra is the capital of Australia.",
                        reference_context="Canberra was officially founded as Australia's capital in 1913.",
                        judge_model=judge,
                    )

                    assert isinstance(res, EvaluationResponse)
                    assert res.faithfulness_score == 0.95
                    assert "claims supported" in res.faithfulness_reason
                    assert res.evaluation_status == "passed"


# =========================================================================
# 2. Answer Relevancy Metric Test
# =========================================================================
def test_answer_relevancy_metric_evaluation(eval_service):
    """2. Test successful answer relevancy evaluation."""
    judge = DummyJudgeModel()
    with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.measure"), \
         patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.measure"), \
         patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.measure"):

        with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.score", 0.85), \
             patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.reason", "Supported."), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.score", 0.92), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.reason", "Output addresses all constraints."), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.score", 0.90), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.reason", "No hallucination detected."):

            res = eval_service.evaluate_single(
                question="Explain QuickSort complexity.",
                actual_response="QuickSort average time complexity is O(n log n).",
                reference_context="QuickSort average time complexity is O(n log n).",
                judge_model=judge,
            )

            assert res.answer_relevancy_score == 0.92
            assert "Output addresses" in res.answer_relevancy_reason
            assert res.evaluation_status == "passed"


# =========================================================================
# 3. Hallucination Metric & Risk Test
# =========================================================================
def test_hallucination_metric_evaluation(eval_service):
    """3. Test hallucination score and inverted risk calculation."""
    judge = DummyJudgeModel()
    with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.measure"), \
         patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.measure"), \
         patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.measure"):

        # In DeepEval 4.x, score = 0.80 means 80% factual agreement -> risk is 1 - 0.80 = 0.20
        with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.score", 0.80), \
             patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.reason", "Supported."), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.score", 0.85), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.reason", "Relevant."), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.score", 0.80), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.reason", "80% of statements match context."):

            res = eval_service.evaluate_single(
                question="What is the speed of sound?",
                actual_response="Sound travels at 343 m/s in air at 20 degrees Celsius.",
                reference_context="The speed of sound in dry air at 20 °C is 343 metres per second.",
                judge_model=judge,
            )

            assert res.hallucination_score == 0.80
            assert res.hallucination_risk == 0.20
            assert "80% of statements" in res.hallucination_reason


# =========================================================================
# 4. Missing Gemini API Configuration Handling
# =========================================================================
def test_missing_gemini_api_configuration(eval_service):
    """4. Test missing GEMINI_API_KEY returns awaiting_api_key status without crashing."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        res = eval_service.evaluate_single(
            question="What is DNS?",
            actual_response="Domain Name System.",
            reference_context="DNS translates domain names to IP addresses.",
            judge_model=None,
        )

        assert res.evaluation_status == "awaiting_api_key"
        assert res.faithfulness_score is None
        assert "Awaiting Gemini API Configuration" in res.error


# =========================================================================
# 5. Invalid Evaluation Input Validation
# =========================================================================
def test_invalid_evaluation_input(eval_service):
    """5. Test that empty questions or responses raise HTTP 400."""
    judge = DummyJudgeModel()

    with pytest.raises(HTTPException) as exc1:
        eval_service.evaluate_single(
            question="",
            actual_response="Valid response",
            reference_context="Valid context",
            judge_model=judge,
        )
    assert exc1.value.status_code == 400

    with pytest.raises(HTTPException) as exc2:
        eval_service.evaluate_single(
            question="Valid question",
            actual_response="   ",
            reference_context="Valid context",
            judge_model=judge,
        )
    assert exc2.value.status_code == 400


# =========================================================================
# 6. Missing Reference Context Validation
# =========================================================================
def test_missing_reference_context(eval_service):
    """6. Test that empty reference context raises HTTP 400."""
    judge = DummyJudgeModel()

    with pytest.raises(HTTPException) as exc:
        eval_service.evaluate_single(
            question="What is TCP?",
            actual_response="Transmission Control Protocol",
            reference_context="",
            judge_model=judge,
        )
    assert exc.value.status_code == 400
    assert "Reference context cannot be empty" in exc.value.detail


# =========================================================================
# 7. Benchmark Dataset Loading Test
# =========================================================================
def test_benchmark_dataset_loading(eval_service):
    """7. Test benchmark dataset exists, is valid JSON, and has >= 25 test cases."""
    path = eval_service._locate_dataset_path()
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 25

    # Verify schema of test cases
    sample = data[0]
    assert "test_id" in sample
    assert "category" in sample
    assert "input" in sample
    assert "expected_output" in sample
    assert "reference_context" in sample
    assert "evaluation_criteria" in sample


# =========================================================================
# 8. Benchmark Result Aggregation Test
# =========================================================================
def test_benchmark_result_aggregation(eval_service):
    """8. Test running benchmark on sample cases aggregates results accurately."""
    judge = DummyJudgeModel()

    with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.measure"), \
         patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.measure"), \
         patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.measure"):

        with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.score", 0.90), \
             patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.reason", "Faithful."), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.score", 0.85), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.reason", "Relevant."), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.score", 0.95), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.reason", "Accurate."):

            summary = eval_service.run_benchmark(sample_size=3, judge_model=judge)

            assert isinstance(summary, BenchmarkSummary)
            assert summary.total_cases == 3
            assert summary.passed_cases == 3
            assert summary.failed_cases == 0
            assert summary.average_faithfulness == 0.90
            assert summary.average_answer_relevancy == 0.85
            assert summary.average_hallucination_score == 0.95
            assert summary.average_hallucination_risk == 0.05
            assert summary.report_path is not None
            assert os.path.exists(summary.report_path)


# =========================================================================
# 9. Evaluation History Retrieval Test
# =========================================================================
def test_evaluation_history_retrieval(eval_service):
    """9. Test history records are tracked and retrieved with limit and filters."""
    judge = DummyJudgeModel()

    with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.measure"), \
         patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.measure"), \
         patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.measure"):

        with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.score", 0.80), \
             patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.reason", "Good."), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.score", 0.80), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.reason", "Good."), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.score", 0.80), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.reason", "Good."):

            eval_service.evaluate_single(
                question="Q1", actual_response="A1", reference_context="C1", category="Computer Science", judge_model=judge
            )
            eval_service.evaluate_single(
                question="Q2", actual_response="A2", reference_context="C2", category="Mathematics", judge_model=judge
            )

    history = eval_service.get_history(limit=10)
    assert len(history) == 2

    # Filter by category
    cs_history = eval_service.get_history(category_filter="Computer Science")
    assert len(cs_history) == 1
    assert cs_history[0].category == "Computer Science"


# =========================================================================
# 10. Evaluation Summary Generation Test
# =========================================================================
def test_evaluation_summary_generation(eval_service):
    """10. Test summary aggregation calculates accurate metric averages."""
    judge = DummyJudgeModel()

    with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.measure"), \
         patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.measure"), \
         patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.measure"):

        with patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.score", 0.80), \
             patch("deepeval.metrics.faithfulness.faithfulness.FaithfulnessMetric.reason", "Good."), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.score", 0.70), \
             patch("deepeval.metrics.answer_relevancy.answer_relevancy.AnswerRelevancyMetric.reason", "Good."), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.score", 0.90), \
             patch("deepeval.metrics.hallucination.hallucination.HallucinationMetric.reason", "Good."):

            eval_service.evaluate_single(
                question="Q1", actual_response="A1", reference_context="C1", judge_model=judge
            )

    summary = eval_service.get_summary()
    assert summary.total_evaluations == 1
    assert summary.average_faithfulness == 0.80
    assert summary.average_answer_relevancy == 0.70
    assert summary.average_hallucination_score == 0.90
    assert summary.average_hallucination_risk == 0.10
    assert summary.successful_evaluations == 1
    assert summary.failed_evaluations == 0


# =========================================================================
# 11. Phase 7: Unconfigured API Key Non-Fabrication Test
# =========================================================================
def test_evaluation_unconfigured_api_key_handling(eval_service):
    """Phase 7: Test that unconfigured GEMINI_API_KEY returns awaiting_api_key without fabricated scores."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        res = eval_service.evaluate_single(
            question="What is the speed of light?",
            actual_response="Approximately 300,000 km/s.",
            reference_context="Light travels at 299,792,458 meters per second in vacuum.",
            judge_model=None,
        )

        assert res.evaluation_status == "awaiting_api_key"
        assert res.faithfulness_score is None
        assert res.answer_relevancy_score is None
        assert res.hallucination_score is None
        assert res.hallucination_risk is None
        assert "Awaiting Gemini API Configuration" in (res.error or "")
