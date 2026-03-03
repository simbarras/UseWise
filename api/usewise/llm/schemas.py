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

def get_flash_summary_message(
    yes_no_questions: list[str],
) -> str:
    questions_block = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(yes_no_questions)
    )

    return f"""
Analyze the privacy policy provided in the system message.

Your task is to extract structured information.

1) For each of the following yes/no statements:
   - Answer with true or false.
   - Use true only if the policy clearly confirms the statement.
   - If the policy does not mention it or is unclear, answer false.
   - Keep the same order.

YES/NO STATEMENTS:
{questions_block}

2) Determine how long user data is stored.
   Provide a short human-readable phrase (e.g., "1 year",
   "Until account deletion", "Indefinitely").

3) Provide an overall privacy risk score from 1 (very low risk)
   to 10 (very high risk), considering:
   - Data sharing
   - Tracking technologies
   - Data retention duration
   - User rights (e.g., deletion)

Return only structured data matching the expected schema.
"""

class FlashSummaryOutput(BaseModel):
    flags: Annotated[
        list[bool],
        Field(
            min_length=4,
            max_length=4,
            description=(
                "Boolean answers to the yes/no privacy questions, "
                "in the exact same order as provided. "
                "Use true if the policy confirms the statement, "
                "false otherwise."
            ),
        ),
    ]

    storage_info: str = Field(
        ...,
        description=(
            "Short human-readable description of how long user data "
            "is retained (e.g. '1 year', '6 months', "
            "'Until account deletion', 'Indefinitely')."
        ),
    )

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



json_prompt_raw_template = """Return a JSON object that matches this structure:
{format_instructions}

Question: {question}
        """

def get_json_prompt_template(
    parser: PydanticOutputParser[FlashSummaryOutput],
) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        json_prompt_raw_template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
