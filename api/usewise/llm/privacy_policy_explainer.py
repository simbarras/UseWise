import os
from collections.abc import Iterator

from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.messages import BaseMessageChunk, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from usewise.llm.config import llm_url, model_name
from usewise.llm.prompt import get_system_message


class PrivacyPolicyExplainer:
    def __init__(self, privacy_policy: str)-> None:
        self.system_msg = get_system_message(privacy_policy=privacy_policy)
        self.llm = ChatOpenAI(
            model=model_name,
            base_url=llm_url,
            api_key=SecretStr(os.environ["GROQ_API_KEY"]),
            callbacks=[StreamingStdOutCallbackHandler()]
        )

    def invoke(self, question: str) -> Iterator[BaseMessageChunk]:

        messages = [
            self.system_msg,
            HumanMessage(content=question)
        ]

        return self.llm.stream(messages)
