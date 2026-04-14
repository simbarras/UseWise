from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from usewise.db.models import Base, Feedback

RISK_LEVEL_QUESTION = "risk_level"

_DB_PATH = Path(__file__).parent.parent.parent / "usewise_feedback.db"
_engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
)
_SessionLocal = sessionmaker(bind=_engine)


def init_db() -> None:
    Base.metadata.create_all(_engine)


def get_db() -> Generator[Session, None, None]:
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_response_stats_bool(
    policy: str, question: str, db: Session
) -> tuple[bool | None, int, int]:
    """Return (majority_value, total_count, majority_percentage) for a boolean question.

    Returns (None, 0, 0) when no feedback exists yet.
    majority_value is True when >= 50% of users answered True.
    majority_percentage is the percentage of votes for the majority answer.
    """
    result = (
        db.query(Feedback.user_value)
        .filter(
            Feedback.policy_fingerprint == policy,
            Feedback.question == question,
        )
        .all()
    )
    values = [row[0] for row in result]
    total = len(values)
    if total == 0:
        return None, 0, 0
    mean = sum(values) / total
    majority = mean >= 0.5  # noqa: PLR2004
    percentage = round(mean * 100) if majority else round((1 - mean) * 100)
    return majority, total, percentage


def get_user_risk_stats(policy: str, db: Session) -> tuple[float | None, int]:
    """Return (average_value, total_count) for risk level feedback (1-5 scale).

    Returns (None, 0) when no feedback exists yet.
    """
    result = (
        db.query(Feedback.user_value)
        .filter(
            Feedback.policy_fingerprint == policy,
            Feedback.question == RISK_LEVEL_QUESTION,
        )
        .all()
    )
    values = [row[0] for row in result]
    total = len(values)
    if total == 0:
        return None, 0
    return sum(values) / total, total
