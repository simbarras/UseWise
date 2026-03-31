import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from usewise.llm import config
from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer
from usewise.llm.schemas import FlashSummaryReturnType

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

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


@app.post("/summary/")
async def get_summary(pp: PrivacyPolicy) -> PPSummary:
    """
    Discussion with Manuel for the API:

    model = pp.model or "default-model"
    ai = Aisummarizer(pp.content, model)
    summaries:  = ai.flash_summary(questions = [{question, returnType}, ])
    # questions = ai.generate_questions()
    ai_response = ai.get_ai_question_responses(questions = ["question1", "question2"])

    result = PPSummary(
        risk_level=risk_level,
        summaries=summaries,
        ai=ai_response
    )
    return result
    """
    model = pp.model or config.model_name
    if model not in config.models:
        error_msg = f"Model '{pp.model}' is not supported."
        raise ValueError(error_msg)

    ppe = PrivacyPolicyExplainer(privacy_policy=pp.content, model_name=model)

    ppe_summary = ppe.get_flash_summary(questions=flash_summary_questions)

    return_summary = []
    for i in range(len(ppe_summary.answers)):
        answer = ppe_summary.answers[i]
        question = flash_summary_questions[i][0]
        return_summary.append(
            Summaries(
                flash=question,
                value=answer.value,
            )
        )

    follow_up_responses = []
    for question in follow_up_questions:
        response = ppe.get_questions_answers([question])[0]
        follow_up_responses.append(
            AiQuestion(
                question=question,
                response=response,
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
