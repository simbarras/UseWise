from pathlib import Path
from typing import Any

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from usewise.llm.config import llm_url, model_name
from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer
from usewise.llm.schemas import FlashSummaryReturnType


def _sample_privacy_policy() -> str:
    with Path("test_data/sample_privacy_policy.txt").open() as f:
        return f.read()


def test_privacy_policy_explainer_initialization_uses_config_and_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            created.update(kwargs)

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, model_name)

    assert isinstance(explainer.system_msg, SystemMessage)
    assert "Usewise AG" in explainer.system_msg.content
    assert created["model"] == model_name
    assert created["base_url"] == llm_url
    assert created["api_key"].get_secret_value() == "test-api-key"


def test_privacy_policy_explainer_flash_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        content = '{"flags":[true,false,true],"times":["24 months"],"score":7}'

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def invoke(self, _messages: list[Any]) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, model_name)

    questions: list[tuple[str, FlashSummaryReturnType]] = [
        ("Data is shared with third parties.", FlashSummaryReturnType.FLAG),
        ("Cookies are used.", FlashSummaryReturnType.FLAG),
        ("Users can request deletion.", FlashSummaryReturnType.FLAG),
        ("How long are inactive accounts retained?", FlashSummaryReturnType.TIME),
    ]

    result = explainer.get_flash_summary(questions)

    assert result.score == 7
    assert len(result.answers) == len(questions)
    assert result.answers[0].value is True
    assert result.answers[1].value is False
    assert result.answers[2].value is True
    assert result.answers[3].value == "24 months"
    assert result.answers[3].type == FlashSummaryReturnType.TIME


def test_privacy_policy_explainer_invoke_uses_system_and_human_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_messages: list[Any] = []

    class FakeResponse:
        content = "Mock answer"

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def invoke(self, messages: list[Any]) -> FakeResponse:
            captured_messages.extend(messages)
            return FakeResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, model_name)
    result = explainer.invoke("Can I use this commercially?")

    assert result == "Mock answer"
    assert isinstance(captured_messages[0], SystemMessage)
    assert isinstance(captured_messages[1], HumanMessage)
    assert captured_messages[1].content == "Can I use this commercially?"


def test_get_questions_answers_returns_one_answer_per_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __init__(self, content: str) -> None:
            self.content = content

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def invoke(self, messages: list[Any]) -> FakeResponse:
            question = messages[1].content
            return FakeResponse(f"answer:{question}")

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, model_name)
    questions = ["Q1?", "Q2?"]

    result = explainer.get_questions_answers(questions)

    assert result == ["answer:Q1?", "answer:Q2?"]


def test_get_flash_summary_raises_type_error_for_invalid_question_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def invoke(self, _messages: list[Any]) -> Any:
            raise AssertionError("Model should not be called for invalid question types")

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, model_name)

    bad_questions: list[tuple[str, Any]] = [
        ("Invalid question type", "unknown"),
    ]

    with pytest.raises(TypeError):
        explainer.get_flash_summary(bad_questions)  # type: ignore[arg-type]


def test_reassemble_questions_raises_type_error_for_invalid_question_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy, model_name)

    bad_questions: list[tuple[str, Any]] = [
        ("Q1", FlashSummaryReturnType.FLAG),
        ("Q2", "unknown"),
    ]

    with pytest.raises(TypeError):
        explainer.reassemble_questions(  # type: ignore[arg-type]
            flags=[True],
            times=[],
            questions=bad_questions,
        )
