import os

from dotenv import load_dotenv
from pydantic import SecretStr

models = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "groq/compound",
]
model_name = models[0]
fallback_model_name = models[1]

llm_url = "https://api.groq.com/openai/v1"#"https://openrouter.ai/api/v1"


load_dotenv()


def get_groq_api_key() -> SecretStr:
    return SecretStr(os.environ["GROQ_API_KEY"])


def get_openrouter_api_key() -> SecretStr:
    return SecretStr(os.environ["OPEN_ROUTER_API_KEY"])
