import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from openai import RateLimitError
from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer
from usewise.llm.schemas import FlashSummary, FlashSummaryAnswer, FlashSummaryReturnType


def _sample_privacy_policy() -> str:
    with Path("test_data/sample_privacy_policy.txt").open() as f:
        return f.read()


def test_divide_questions_separates_flags_and_times(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    questions = [
        ("Is data shared?", FlashSummaryReturnType.FLAG),
        ("How long is data stored?", FlashSummaryReturnType.TIME),
        ("Are cookies used?", FlashSummaryReturnType.FLAG),
        ("Retention period?", FlashSummaryReturnType.TIME),
    ]

    flags, times = explainer.divide_questions(questions)

    assert len(flags) == 2
    assert len(times) == 2
    assert flags[0] == "Is data shared?"
    assert flags[1] == "Are cookies used?"
    assert times[0] == "How long is data stored?"
    assert times[1] == "Retention period?"


def test_divide_questions_raises_on_invalid_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    bad_questions: list[tuple[str, Any]] = [
        ("Question?", "invalid_type"),
    ]

    with pytest.raises(TypeError):
        explainer.divide_questions(bad_questions)  # type: ignore[arg-type]


def test_reassemble_questions_preserves_answer_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    questions = [
        ("Flag 1?", FlashSummaryReturnType.FLAG),
        ("Time 1?", FlashSummaryReturnType.TIME),
        ("Flag 2?", FlashSummaryReturnType.FLAG),
    ]

    answers = explainer.reassemble_questions(
        flags=[True, False],
        times=["24 months"],
        questions=questions,
    )

    assert len(answers) == 3
    assert answers[0].value is True
    assert answers[0].type == FlashSummaryReturnType.FLAG
    assert answers[1].value == "24 months"
    assert answers[1].type == FlashSummaryReturnType.TIME
    assert answers[2].value is False
    assert answers[2].type == FlashSummaryReturnType.FLAG



def test_format_flash_summary_memory_includes_all_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    questions = [
        ("Is data shared?", FlashSummaryReturnType.FLAG),
        ("How long stored?", FlashSummaryReturnType.TIME),
    ]
    answers = [
        FlashSummaryAnswer(value=True, type=FlashSummaryReturnType.FLAG),
        FlashSummaryAnswer(value="24 months", type=FlashSummaryReturnType.TIME),
    ]
    summary = FlashSummary(answers=answers, score=7)

    memory = explainer._format_flash_summary_memory(questions, summary)

    assert "Is data shared?: True" in memory
    assert "How long stored?: 24 months" in memory
    assert "Privacy risk score: 7/10" in memory


def test_get_combined_summary_calls_llm_with_questions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_messages: list[list[Any]] = []

    class FakeResponse:
        content = '{"flags":[true,false,true,false],"times":["12 months"],"follow_up_answers":["Answer 1","Answer 2"]}'

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def invoke(self, messages: list[Any]) -> FakeResponse:
            captured_messages.append(list(messages))
            return FakeResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    questions = [
        ("User data is not shared with third parties?", FlashSummaryReturnType.FLAG),
        ("Profiling or commercial cookies are not used?", FlashSummaryReturnType.FLAG),
        ("How long is the user data stored?", FlashSummaryReturnType.TIME),
        ("The user can request deletion of their data?", FlashSummaryReturnType.FLAG),
        ("Users are notified or can see any policy changes?", FlashSummaryReturnType.FLAG),
    ]
    follow_up = ["Why?", "How?"]

    summary, follow_ups = explainer.get_combined_summary(questions, follow_up)

    assert 1 <= summary.score <= 5
    assert len(summary.answers) == 5
    assert len(follow_ups) == 2


def test_get_combined_summary_returns_correct_answer_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        content = '{"flags":[true,false,true,false],"times":["6 months"],"follow_up_answers":["A1","A2"]}'

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def invoke(self, messages: list[Any]) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    questions = [
        ("User data is not shared with third parties?", FlashSummaryReturnType.FLAG),
        ("Profiling or commercial cookies are not used?", FlashSummaryReturnType.FLAG),
        ("How long is the user data stored?", FlashSummaryReturnType.TIME),
        ("The user can request deletion of their data?", FlashSummaryReturnType.FLAG),
        ("Users are notified or can see any policy changes?", FlashSummaryReturnType.FLAG),
    ]

    summary, _ = explainer.get_combined_summary(questions, [])

    assert summary.answers[0].type == FlashSummaryReturnType.FLAG
    assert summary.answers[0].value is True
    assert summary.answers[1].type == FlashSummaryReturnType.FLAG
    assert summary.answers[1].value is False
    assert summary.answers[2].type == FlashSummaryReturnType.TIME
    assert summary.answers[2].value == "6 months"
    assert summary.answers[3].type == FlashSummaryReturnType.FLAG
    assert summary.answers[3].value is True
    assert summary.answers[4].type == FlashSummaryReturnType.FLAG
    assert summary.answers[4].value is False


def test_reassemble_questions_raises_on_invalid_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    bad_questions: list[tuple[str, Any]] = [
        ("Q1", FlashSummaryReturnType.FLAG),
        ("Q2", "invalid_type"),
    ]

    with pytest.raises(TypeError):
        explainer.reassemble_questions(
            flags=[True],
            times=[],
            questions=bad_questions,  # type: ignore[arg-type]
        )


def test_get_combined_summary_handles_rate_limit_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:

    class FakeResponse:
        content = '{"flags":[true,false,true,false],"times":["6 months"],"follow_up_answers":["Fallback response"]}'

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            self.model_name = kwargs.get("model", "test-model")

        def invoke(self, messages: list[Any]) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, "test-model")

    questions = [
        ("User data is not shared with third parties?", FlashSummaryReturnType.FLAG),
        ("Profiling or commercial cookies are not used?", FlashSummaryReturnType.FLAG),
        ("How long is the user data stored?", FlashSummaryReturnType.TIME),
        ("The user can request deletion of their data?", FlashSummaryReturnType.FLAG),
        ("Users are notified or can see any policy changes?", FlashSummaryReturnType.FLAG),
    ]

    with caplog.at_level(logging.WARNING), patch.object(explainer.model, "invoke") as mock_invoke:
        mock_invoke.side_effect = [
            RateLimitError(message="Rate limit", response=MagicMock(), body={}),
            FakeResponse(),
        ]

        summary, follow_ups = explainer.get_combined_summary(questions, [])

    assert 1 <= summary.score <= 5
    assert len(follow_ups) == 1
    assert "Rate limit hit" in caplog.text
    assert "falling back" in caplog.text
