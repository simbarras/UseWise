import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from usewise.db.database import get_db, get_user_response_stats_bool, init_db
from usewise.db.models import Feedback
from usewise.llm import config
from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer
from usewise.llm.schemas import FlashSummaryReturnType
from usewise.restApi.utils import resolve_content

logger = logging.getLogger(__name__)

DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ─── Request / response models ────────────────────────────────────────────────


class PrivacyPolicy(BaseModel):
    content: str
    model: str | None = None


class AiQuestion(BaseModel):
    question: str
    response: str


class Summaries(BaseModel):
    flash: str
    value: Any
    user_count: int
    user_estimation: bool | None


class PPSummary(BaseModel):
    risk_level: int
    summaries: list[Summaries]
    ai: list[AiQuestion]
    model_used: str
    session_key: str
    policy_fingerprint: str


class FeedbackRequest(BaseModel):
    session_key: str
    policy_fingerprint: str
    question: str
    user_value: int  # 0 = False, 1 = True


# ─── Static question lists ────────────────────────────────────────────────────

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


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _fingerprint(content: str) -> str:
    return content[:50].replace("\n", " ")


def _get_flash_summary(
    ppe: PrivacyPolicyExplainer, policy: str, db: Session
) -> tuple[list[Summaries], int]:
    ppe_summary = ppe.get_flash_summary(questions=flash_summary_questions)
    return_summary = []
    for i, answer in enumerate(ppe_summary.answers):
        question = flash_summary_questions[i][0]
        prediction, user_count = get_user_response_stats_bool(
            policy=policy,
            question=question,
            db=db,
        )
        return_summary.append(
            Summaries(
                flash=question,
                value=answer.value,
                user_count=user_count,
                user_estimation=prediction,
            )
        )
    return return_summary, ppe_summary.score


def _get_follow_up_responses(ppe: PrivacyPolicyExplainer) -> list[AiQuestion]:
    follow_up_responses = []
    for question in follow_up_questions:
        response = ppe.get_questions_answers([question])[0]
        follow_up_responses.append(AiQuestion(question=question, response=response))
    return follow_up_responses


# ─── Routes ───────────────────────────────────────────────────────────────────


@app.post("/summary/")
async def get_summary(pp: PrivacyPolicy, db: DbSession) -> PPSummary:
    model = pp.model or config.model_name
    if model not in config.models:
        error_msg = f"Model '{pp.model}' is not supported."
        raise ValueError(error_msg)

    content = resolve_content(pp.content)
    policy_fingerprint = _fingerprint(content)
    session_key = str(uuid.uuid4())

    ppe = PrivacyPolicyExplainer(privacy_policy=content, model_name=model)
    return_summary, risk_level = _get_flash_summary(ppe, policy_fingerprint, db)
    follow_up_responses = _get_follow_up_responses(ppe)

    return PPSummary(
        risk_level=risk_level,
        summaries=return_summary,
        ai=follow_up_responses,
        model_used=model,
        session_key=session_key,
        policy_fingerprint=policy_fingerprint,
    )


class FeedbackResponse(BaseModel):
    user_count: int
    user_estimation: bool | None


@app.post("/feedback/")
async def submit_feedback(req: FeedbackRequest, db: DbSession) -> FeedbackResponse:
    stmt = (
        sqlite_insert(Feedback)
        .values(
            session_key=req.session_key,
            policy_fingerprint=req.policy_fingerprint,
            question=req.question,
            user_value=req.user_value,
        )
        .on_conflict_do_update(
            index_elements=["session_key", "question"],
            set_={"user_value": req.user_value},
        )
    )
    db.execute(stmt)
    db.commit()

    estimation, total = get_user_response_stats_bool(
        policy=req.policy_fingerprint, question=req.question, db=db
    )
    return FeedbackResponse(user_count=total, user_estimation=estimation)


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
