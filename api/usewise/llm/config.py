import os

from dotenv import load_dotenv
from pydantic import SecretStr

models = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2-instruct",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-prompt-guard-2-86m",
]
model_name = models[-1]

llm_url = "https://api.groq.com/openai/v1"


load_dotenv()


def get_groq_api_key() -> SecretStr:
    return SecretStr(os.environ["GROQ_API_KEY"])
