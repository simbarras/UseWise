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


def test_get_system_message_is_privacy_analyst() -> None:
    message = get_system_message()

    assert message.content is not None
    assert "privacy policy analyst" in message.content


def test_get_system_message_with_prior_feedback_context() -> None:
    feedback_context = "Previous analysis showed high risk."

    message = get_system_message(feedback_context)

    assert message.content is not None
    assert feedback_context in message.content


def test_get_system_message_without_feedback_context() -> None:
    message = get_system_message(None)

    assert message.content is not None
    assert "privacy policy analyst" in message.content
