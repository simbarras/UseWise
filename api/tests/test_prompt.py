from langchain_core.messages import SystemMessage

from usewise.llm.prompt import get_system_message


def test_get_system_message_contains_privacy_policy_text() -> None:
    privacy_policy_text = "Privacy Policy"

    message = get_system_message(privacy_policy=privacy_policy_text)

    assert isinstance(message, SystemMessage)
    assert privacy_policy_text in message.content
