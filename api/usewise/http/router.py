import logging

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


app = FastAPI()

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
async def get_summary(pp: PrivacyPolicy):
    logger.info(f"Received privacy policy content: {pp.content}")
    result = PPSummary(
        risk_level=3,
        summaries=[
            Summaries(flash="This is a flash summary.", present=True),
            Summaries(flash="This is another flash summary.", present=False)
        ],
        ai=[
            AiQuestion(question="What is the data retention period?", response="The data retention period is 30 days."),
            AiQuestion(question="Is user data shared with third parties?", response="No, user data is not shared with third parties.")
        ]
    )
    return result

@app.get("/health/")
async def health_check():
    return {"status": "ok"}