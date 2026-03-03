from pathlib import Path
from typing import Any

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from usewise.llm.config import llm_url, model_name
from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer


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
    explainer = PrivacyPolicyExplainer(privacy_policy)

    assert isinstance(explainer.system_msg, SystemMessage)
    assert "Usewise AG" in explainer.system_msg.content
    assert created["model"] == model_name
    assert created["base_url"] == llm_url
    assert created["api_key"].get_secret_value() == "test-api-key"

def test_privacy_policy_explainer_flash_summaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        content = '{"flags":[true,false,true,false,true],"storage_info":"12 months","score":7}'

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def invoke(self, _messages: list[Any]) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy)
    yes_no_questions = [
        "Does the policy allow selling personal data?",
        "Does the policy specify a retention period?",
        "Can users request deletion of their data?",
        "Is data shared with third parties?",
        "Are cross-border transfers possible?",
    ]
    result = explainer.flash_summary(yes_no_questions)

    assert result.flags == [True, False, True, False, True]
    assert result.storage_info == "12 months"
    assert result.score == 7

def test_privacy_policy_explainer_invoke_streams_with_system_and_human_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_messages: list[Any] = []

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def stream(self, messages: list[Any]) -> list[str]:
            captured_messages.extend(messages)
            return ["chunk-1", "chunk-2"]

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    privacy_policy = _sample_privacy_policy()
    explainer = PrivacyPolicyExplainer(privacy_policy)
    result = explainer.ask_question("Can I use this commercially?")

    assert result == ["chunk-1", "chunk-2"]
    assert isinstance(captured_messages[0], SystemMessage)
    assert isinstance(captured_messages[1], HumanMessage)
    assert captured_messages[1].content == "Can I use this commercially?"
