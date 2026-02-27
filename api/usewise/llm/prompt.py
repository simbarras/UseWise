from langchain_core.messages import SystemMessage


def get_system_message(privacy_policy: str) -> SystemMessage:
    return SystemMessage(
        content=(
            "You are a helpful assistant that answers questions on "
            "the following privacy policy:\n\n"
            f"{privacy_policy}"
        )
    )
