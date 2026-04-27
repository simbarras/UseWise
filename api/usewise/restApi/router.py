import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from usewise.llm import config
from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer
from usewise.llm.schemas import FlashSummaryReturnType
from usewise.restApi.utils import resolve_content

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # Your frontend URLs
    allow_methods=["GET", "POST"],  # Or *
    allow_headers=["Content-Type"],  # Or *
    # can add: allow_credentials=True,
)


# This defines the structure of your request body
class PrivacyPolicy(BaseModel):
    content: str
    model: str | None = None


class AiQuestion(BaseModel):
    question: str
    response: str


class Summaries(BaseModel):
    flash: str
    value: Any


class PPSummary(BaseModel):
    risk_level: int
    summaries: list[Summaries]
    ai: list[AiQuestion]
    model_used: str


flash_summary_questions = [
    ("User data is not shared with third parties.", FlashSummaryReturnType.FLAG),
    ("Profiling or commercial cookies are not used.", FlashSummaryReturnType.FLAG),
    ("How long is the user data stored?", FlashSummaryReturnType.TIME),
    ("The user can request deletion of their data.", FlashSummaryReturnType.FLAG),
    ("Users are notified or can see any policy changes.", FlashSummaryReturnType.FLAG),
]


follow_up_questions = [
    "Why did you choose this score of risk level ?",
    "What are the third parties that the data is shared with?",
    "What kind of cookies or tracking technologies are used?",
    "How can I request deletion of my data?",
]


### START: Convert None to False (UI compatibility)
### TODO: Remove this entire block once the UI supports null/undefined states
def convert_none_to_false(flags: list[bool | None]) -> list[bool]:
    """Convert None values to False for UI compatibility.

    TODO: Remove this conversion once the UI supports null/undefined states.
    This is a temporary measure to handle LLM uncertainty (None) as False.
    """
    return [flag if flag is not None else False for flag in flags]
### END: Convert None to False


@app.post("/summary/")
async def get_summary(pp: PrivacyPolicy) -> PPSummary:
    model = pp.model or config.model_name
    if model not in config.models:
        error_msg = f"Model '{pp.model}' is not supported."
        raise ValueError(error_msg)

    content = resolve_content(pp.content)

    ppe = PrivacyPolicyExplainer(privacy_policy=content, model_name=model)

    ppe_summary, follow_up_answers = ppe.get_combined_summary(
        questions=flash_summary_questions,
        follow_up_questions=follow_up_questions,
    )

    return_summary = []
    for i in range(len(ppe_summary.answers)):
        answer = ppe_summary.answers[i]
        question = flash_summary_questions[i][0]
        value = answer.value
        ### START: Convert None to False (UI compatibility)
        if isinstance(value, (bool, type(None))):
            value = convert_none_to_false([value])[0]
        ### END: Convert None to False
        return_summary.append(
            Summaries(
                flash=question,
                value=value,
            )
        )

    follow_up_responses = []
    for i, question in enumerate(follow_up_questions):
        follow_up_responses.append(
            AiQuestion(
                question=question,
                response=follow_up_answers[i],
            )
        )

    return PPSummary(
        risk_level=ppe_summary.score,
        summaries=return_summary,
        ai=follow_up_responses,
        model_used=model,
    )


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
