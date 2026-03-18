import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import llm.config
from llm.privacy_policy_explainer import PrivacyPolicyExplainer
from llm.schemas import FlashSummaryReturnType

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
    ("Data is shared with third parties.", FlashSummaryReturnType.FLAG),
    ("Cookies or tracking technologies are used.", FlashSummaryReturnType.FLAG),
    ("For how much time the data gonna be stored.", FlashSummaryReturnType.TIME),
    ("Users can request deletion of their data.", FlashSummaryReturnType.FLAG),
    ("The policy can change without notice.", FlashSummaryReturnType.FLAG),
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
    model = pp.model or llm.config.model_name
    if model not in llm.config.models:
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

    return PPSummary(
        risk_level=ppe_summary.score,
        summaries=return_summary,
        ai=[
            AiQuestion(
                question="What is the data retention period?",
                response="The data retention period is 30 days (Fake response)",
            ),
            AiQuestion(
                question="Is user data shared with third parties?",
                response="No, user data is not shared with third parties (Fake response)",
            ),
        ],
        model_used=model,
    )


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
