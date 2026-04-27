import logging
import re
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from usewise.db.database import (
    RISK_LEVEL_QUESTION,
    get_db,
    get_user_response_stats_bool,
    get_user_response_stats_time,
    get_user_risk_stats,
    init_db,
)
from usewise.db.models import Feedback
from usewise.llm import config
from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer
from usewise.llm.schemas import TIME_BUCKETS, FlashSummaryReturnType
from usewise.restApi.utils import resolve_content

logger = logging.getLogger(__name__)

DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://usewise.live",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
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
    # FLAG question fields
    user_count: int
    user_estimation: bool | None
    user_percentage: int
    # TIME question fields
    user_time_bucket: int | None = None
    user_time_count: int = 0
    user_time_percentage: int = 0
    llm_time_bucket: int | None = None


class PPSummary(BaseModel):
    risk_level: int
    summaries: list[Summaries]
    ai: list[AiQuestion]
    model_used: str
    session_key: str
    policy_fingerprint: str
    user_risk_count: int
    user_risk_average: float | None


class FeedbackRequest(BaseModel):
    session_key: str
    policy_fingerprint: str
    question: str
    user_value: int  # 0 = False, 1 = True


class FeedbackRiskRequest(BaseModel):
    session_key: str
    policy_fingerprint: str
    user_value: int  # 1-5 scale


class FeedbackTimeRequest(BaseModel):
    session_key: str
    policy_fingerprint: str
    question: str
    user_value: int  # 0-6 bucket index


# ─── Time bucket helpers ──────────────────────────────────────────────────────

_TIME_BUCKETS_LOWER = [b.lower() for b in TIME_BUCKETS]


def _months_to_bucket(months: float) -> int:
    if months < 1:
        return 0
    if months <= 6:  # noqa: PLR2004
        return 1
    if months <= 12:  # noqa: PLR2004
        return 2
    if months <= 36:  # noqa: PLR2004
        return 3
    return 4


def _map_llm_time_to_bucket(value: str) -> int | None:
    """Map an LLM-returned time string to its TIME_BUCKETS index.

    Does a case-insensitive exact match first (LLM should follow the prompt),
    then falls back to keyword/numeric parsing for robustness.
    """
    v = value.strip().lower()

    try:
        return _TIME_BUCKETS_LOWER.index(v)
    except ValueError:
        pass

    if any(k in v for k in ("indefinite", "forever", "no limit", "unlimited")):
        return 5
    if any(k in v for k in ("account", "deletion", "when deleted")):
        return 6

    patterns = [
        (re.search(r"(\d+(?:\.\d+)?)\s*year", v), lambda m: float(m.group(1)) * 12),
        (re.search(r"(\d+)\s*month", v), lambda m: float(m.group(1))),
        (re.search(r"(\d+)\s*day", v), lambda m: float(m.group(1)) / 30),
    ]
    for match, to_months in patterns:
        if match:
            return _months_to_bucket(to_months(match))
    return None


# ─── Static question lists ────────────────────────────────────────────────────

flash_summary_questions = [
    ("User data is not shared with third parties?", FlashSummaryReturnType.FLAG),
    ("Profiling or commercial cookies are not used?", FlashSummaryReturnType.FLAG),
    ("How long is the user data stored?", FlashSummaryReturnType.TIME),
    ("The user can request deletion of their data?", FlashSummaryReturnType.FLAG),
    ("Users are notified or can see any policy changes?", FlashSummaryReturnType.FLAG),
]

follow_up_questions = [
    "Why did you choose this score of risk level ?",
    "What are the third parties that the data is shared with?",
    "What kind of cookies or tracking technologies are used?",
    "How can I request deletion of my data?",
]


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
        risk_level=risk_level,
        summaries=return_summary,
        ai=follow_up_responses,
        model_used=model,
        session_key=session_key,
        policy_fingerprint=policy_fingerprint,
        user_risk_count=user_risk_count,
        user_risk_average=user_risk_average,
    )


class FeedbackResponse(BaseModel):
    user_count: int
    user_estimation: bool | None
    user_percentage: int


class FeedbackRiskResponse(BaseModel):
    user_count: int
    user_average: float | None


@app.post("/feedback/risk/")
async def submit_risk_feedback(
    req: FeedbackRiskRequest, db: DbSession
) -> FeedbackRiskResponse:
    stmt = (
        sqlite_insert(Feedback)
        .values(
            session_key=req.session_key,
            policy_fingerprint=req.policy_fingerprint,
            question=RISK_LEVEL_QUESTION,
            user_value=req.user_value,
        )
        .on_conflict_do_update(
            index_elements=["session_key", "question"],
            set_={"user_value": req.user_value},
        )
    )
    db.execute(stmt)
    db.commit()

    average, total = get_user_risk_stats(policy=req.policy_fingerprint, db=db)
    return FeedbackRiskResponse(user_count=total, user_average=average)


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

    estimation, total, percentage = get_user_response_stats_bool(
        policy=req.policy_fingerprint, question=req.question, db=db
    )
    return FeedbackResponse(
        user_count=total, user_estimation=estimation, user_percentage=percentage
    )


class FeedbackTimeResponse(BaseModel):
    user_count: int
    user_time_bucket: int | None
    user_time_percentage: int


@app.post("/feedback/time/")
async def submit_time_feedback(
    req: FeedbackTimeRequest, db: DbSession
) -> FeedbackTimeResponse:
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

    bucket, total, percentage = get_user_response_stats_time(
        policy=req.policy_fingerprint, question=req.question, db=db
    )
    return FeedbackTimeResponse(
        user_count=total, user_time_bucket=bucket, user_time_percentage=percentage
    )


class FeedbackDeleteRequest(BaseModel):
    session_key: str
    policy_fingerprint: str
    question: str


@app.delete("/feedback/")
async def delete_feedback(req: FeedbackDeleteRequest, db: DbSession) -> FeedbackResponse:
    db.query(Feedback).filter(
        Feedback.session_key == req.session_key,
        Feedback.question == req.question,
    ).delete()
    db.commit()

    estimation, total, percentage = get_user_response_stats_bool(
        policy=req.policy_fingerprint, question=req.question, db=db
    )
    return FeedbackResponse(
        user_count=total, user_estimation=estimation, user_percentage=percentage
    )


@app.delete("/feedback/time/")
async def delete_time_feedback(
    req: FeedbackDeleteRequest, db: DbSession
) -> FeedbackTimeResponse:
    db.query(Feedback).filter(
        Feedback.session_key == req.session_key,
        Feedback.question == req.question,
    ).delete()
    db.commit()

    bucket, total, percentage = get_user_response_stats_time(
        policy=req.policy_fingerprint, question=req.question, db=db
    )
    return FeedbackTimeResponse(
        user_count=total, user_time_bucket=bucket, user_time_percentage=percentage
    )


class FeedbackRiskDeleteRequest(BaseModel):
    session_key: str
    policy_fingerprint: str


@app.delete("/feedback/risk/")
async def delete_risk_feedback(
    req: FeedbackRiskDeleteRequest, db: DbSession
) -> FeedbackRiskResponse:
    db.query(Feedback).filter(
        Feedback.session_key == req.session_key,
        Feedback.question == RISK_LEVEL_QUESTION,
    ).delete()
    db.commit()

    average, total = get_user_risk_stats(policy=req.policy_fingerprint, db=db)
    return FeedbackRiskResponse(user_count=total, user_average=average)


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
