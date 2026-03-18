import logging

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Your frontend URLs
    # allow_credentials=True,
    allow_methods=["GET", "POST"],  # Or *
    allow_headers=["Content-Type"],  # Or *
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
    present: bool


class PPSummary(BaseModel):
    risk_level: int
    summaries: list[Summaries]
    ai: list[AiQuestion]


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
    logger.info("Received privacy policy content: %s", pp.content)
    result = PPSummary(
        risk_level=3,
        summaries=[
            Summaries(flash="This is a flash summary.", present=True),
            Summaries(flash="This is another flash summary.", present=False),
        ],
        ai=[
            AiQuestion(
                question="What is the data retention period?",
                response="The data retention period is 30 days.",
            ),
            AiQuestion(
                question="Is user data shared with third parties?",
                response="No, user data is not shared with third parties.",
            ),
        ],
    )
    return result


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
