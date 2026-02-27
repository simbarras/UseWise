from typing import Any

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer


def test_privacy_policy_explainer_initialization_uses_config_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            created.update(kwargs)

    monkeypatch.setenv("GROQ_API_KEY", "test-api-key")
    monkeypatch.setattr("usewise.llm.privacy_policy_explainer.ChatOpenAI", FakeChatOpenAI)

    explainer = PrivacyPolicyExplainer("BSD-3-Clause")

    assert isinstance(explainer.system_msg, SystemMessage)
    assert "BSD-3-Clause" in explainer.system_msg.content
    assert created["model"] == "llama-3.3-70b-versatile"
    assert created["base_url"] == "https://api.groq.com/openai/v1"
    assert created["api_key"].get_secret_value() == "test-api-key"
    assert isinstance(created["callbacks"], list)


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

    explainer = PrivacyPolicyExplainer("Apache-2.0")
    result = explainer.invoke("Can I use this commercially?")

    assert result == ["chunk-1", "chunk-2"]
    assert isinstance(captured_messages[0], SystemMessage)
    assert isinstance(captured_messages[1], HumanMessage)
    assert captured_messages[1].content == "Can I use this commercially?"
