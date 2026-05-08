import pytest
from usewise.llm import config
from usewise.llm.schemas import (
    get_system_message,
)


def test_get_groq_api_key_retrieves_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    api_key = config.get_groq_api_key()
    assert api_key.get_secret_value() == "test-groq-key"


def test_get_openrouter_api_key_retrieves_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_ROUTER_API_KEY", "test-openrouter-key")
    api_key = config.get_openrouter_api_key()
    assert api_key.get_secret_value() == "test-openrouter-key"


def test_get_system_message_includes_privacy_policy() -> None:
    privacy_policy = "This is a test privacy policy."
    message = get_system_message(privacy_policy)

    assert message.content is not None
    assert "You are a helpful assistant" in message.content
    assert privacy_policy in message.content


def test_get_system_message_with_prior_feedback_context() -> None:
    privacy_policy = "This is a test privacy policy."
    feedback_context = "Previous analysis showed high risk."

    message = get_system_message(privacy_policy, feedback_context)

    assert message.content is not None
    assert privacy_policy in message.content
    assert feedback_context in message.content


def test_get_system_message_without_feedback_context() -> None:
    privacy_policy = "Test policy"

    message = get_system_message(privacy_policy, None)

    assert message.content is not None
    assert privacy_policy in message.content
    assert "Previous analysis" not in message.content
