import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field, SecretStr

load_dotenv()


GROQ_API_KEY = SecretStr(os.environ["GROQ_API_KEY"])


def get_system_message(privacy_policy: str) -> SystemMessage:
    return SystemMessage(
        content=(
            "You are a helpful assistant that answers questions"
            #" on the following privacy policy:\n\n"
            #f"{privacy_policy}"
        )
    )

def get_flash_summary_message() -> str:
    return "give randoms numbers for each field please"

class FlashSummaryOutput(BaseModel):
    flags: list[bool] = Field(
        ...,
        min_items=5,
        max_items=6,
        description="A list of 5-6 booleans"
    )
    storage_info: str = Field(
        ...,
        description="Human-readable description of how long something will be stored"
    )
    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="An integer between 1 and 10"
    )
