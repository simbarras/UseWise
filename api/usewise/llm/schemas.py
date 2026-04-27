from enum import StrEnum
from typing import Annotated

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


def get_system_message(privacy_policy: str) -> SystemMessage:
    return SystemMessage(
        content=(
            "You are a helpful assistant that answers questions"
            " on the following privacy policy:\n\n"
            f"{privacy_policy}"
        )
    )

def get_combined_summary_message(
    yes_no_questions: list[str],
    time_based_questions: list[str],
    follow_up_questions: list[str],
) -> str:
    yes_no_block = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(yes_no_questions)
    )

    time_block = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(time_based_questions)
    )

    follow_up_block = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(follow_up_questions)
    )

    return f"""
Analyze the privacy policy provided in the system message.

Your task is to extract structured information.

1) For each of the following yes/no statements:
   - Answer with true, false, or null.
   - Use true only if the policy clearly confirms the statement.
   - Use false only if the policy clearly contradicts the statement.
   - Use null if the policy does not mention it or is unclear.
   - Keep the same order.

YES/NO STATEMENTS:
{yes_no_block}

2) For each of the following time-related questions:
   - Extract the duration mentioned in the policy.
   - Return a short human-readable phrase
     (e.g., "1 year", "6 months", "30 days",
     "Until account deletion", "Indefinitely").
   - Keep the same order.

TIME QUESTIONS:
{time_block}

3) Based on your analysis, provide an overall privacy risk score
   from 1 (very low risk) to 10 (very high risk).

4) Answer each of the following follow-up questions based on the policy:
   - Provide detailed and informative answers.
   - Keep the same order as provided.

FOLLOW-UP QUESTIONS:
{follow_up_block}

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
        le=10,
        description=(
            "Overall privacy risk score from 1 (very low risk) "
            "to 10 (very high risk), based on data sharing, "
            "tracking, retention length, and user rights."
        ),
    )

class FlashSummaryAnswer(BaseModel):
    value: bool | str | None
    type: FlashSummaryReturnType

class FlashSummary(BaseModel):
    answers: list[FlashSummaryAnswer]
    score: int


class CombinedSummaryLLMOutput(BaseModel):
    flags: Annotated[
        list[bool | None],
        Field(
            description=(
                "Boolean answers to the yes/no privacy questions, "
                "in the exact same order as provided. "
                "Use true if the policy clearly confirms the statement, "
                "false if it clearly contradicts the statement, "
                "and null if the policy is unclear or does not mention it."
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
        le=10,
        description=(
            "Overall privacy risk score from 1 (very low risk) "
            "to 10 (very high risk), based on data sharing, "
            "tracking, retention length, and user rights."
        ),
    )

    follow_up_answers: Annotated[
        list[str],
        Field(
            description=(
                "Detailed answers to the follow-up questions "
                "in the exact same order as provided."
            ),
        ),
    ]


json_prompt_raw_template = """Return a JSON object that matches this structure:
{format_instructions}

Question: {question}
        """

def get_json_prompt_template(
    parser: PydanticOutputParser,
) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        json_prompt_raw_template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
