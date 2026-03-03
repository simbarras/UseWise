from collections.abc import Iterator

from langchain_core.messages import BaseMessageChunk, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from usewise.llm.config import get_groq_api_key, llm_url, model_name
from usewise.llm.schemas import (
    FlashSummaryOutput,
    get_flash_summary_message,
    get_json_prompt_template,
    get_system_message,
)


class PrivacyPolicyExplainer:
    def __init__(self, privacy_policy: str) -> None:
        self.system_msg = get_system_message(privacy_policy=privacy_policy)
        self.model = ChatOpenAI(
            model=model_name,
            base_url=llm_url,
            api_key=get_groq_api_key(),
        )

    def flash_summary(self, yes_no_questions: list[str]) -> FlashSummaryOutput:
        parser = PydanticOutputParser(pydantic_object=FlashSummaryOutput)
        prompt = get_json_prompt_template(parser)
        question = get_flash_summary_message(yes_no_questions)
        messages = prompt.format_messages(question=question)
        response = self.model.invoke(messages)
        text = str(response.content)

        return parser.parse(text)

    def ask_question(self, question: str) -> Iterator[BaseMessageChunk]:

        messages = [
            self.system_msg,
            HumanMessage(content=question)
        ]

        return self.model.stream(messages)
