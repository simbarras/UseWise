from enum import StrEnum
from typing import Annotated

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


def get_system_message(
    privacy_policy: str,
    prior_feedback_context: str | None = None,
) -> SystemMessage:
    content = (
        "You are a helpful assistant that answers questions"
        " on the following privacy policy:\n\n"
        f"{privacy_policy}"
    )
    if prior_feedback_context:
        content += f"\n\n{prior_feedback_context}"
    return SystemMessage(content=content)

TIME_BUCKETS = [
    "< 1 month",
    "1-6 months",
    "6-12 months",
    "1-3 years",
    "3+ years",
    "Indefinitely",
    "When account deleted",
]


def get_flash_summary_message(
    yes_no_questions: list[str],
    time_based_questions: list[str],
) -> str:
    yes_no_block = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(yes_no_questions)
    )

    time_block = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(time_based_questions)
    )

    allowed_times = ", ".join(f'"{b}"' for b in TIME_BUCKETS)

    return f"""
Analyze the privacy policy provided in the system message.

Your task is to extract structured information.

1) For each of the following yes/no statements:
   - Answer with true or false.
   - Use true only if the policy clearly confirms the statement.
   - If the policy does not mention it or is unclear, answer false.
   - Keep the same order.

YES/NO STATEMENTS:
{yes_no_block}

2) For each of the following time-related questions:
   - Pick exactly one value from this list: {allowed_times}
   - Choose the closest match to what the policy states.
   - Keep the same order.

TIME QUESTIONS:
{time_block}

3) Based on your analysis, provide an overall privacy risk score
   from 1 (very low risk) to 5 (very high risk).

Return only structured data matching the expected schema.
"""


class FlashSummaryReturnType(StrEnum):
    FLAG = "flag"
    TIME = "time"

class FlashSummaryLLMOutput(BaseModel):
    flags: Annotated[
        list[bool],
        Field(
            description=(
                "Boolean answers to the yes/no privacy questions, "
                "in the exact same order as provided. "
                "Use true if the policy confirms the statement, "
                "false otherwise."
            ),
        ),
    ]

    times: Annotated[
        list[str],
        Field(
            description=(
                "Short human-readable descriptions of a time "
                "duration or time limit "
                "(e.g. '1 year', '6 months', '3 days', "
                "'Until account deletion', 'Indefinitely')."
            ),
        )
    ]

    score: int = Field(
        ...,
        ge=1,
        le=5,
        description=(
            "Overall privacy risk score from 1 (very low risk) "
            "to 5 (very high risk), based on data sharing, "
            "tracking, retention length, and user rights."
        ),
    )

class FlashSummaryAnswer(BaseModel):
    value: bool | str
    type: FlashSummaryReturnType

class FlashSummary(BaseModel):
    answers: list[FlashSummaryAnswer]
    score: int


json_prompt_raw_template = """Return a JSON object that matches this structure:
{format_instructions}

Question: {question}
        """

def get_json_prompt_template(
    parser: PydanticOutputParser[FlashSummaryLLMOutput],
) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        json_prompt_raw_template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
