from collections.abc import Iterator

from langchain_core.messages import BaseMessageChunk, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from usewise.llm.config import llm_url, model_name
from usewise.llm.schemas import (
    GROQ_API_KEY,
    FlashSummaryOutput,
    get_flash_summary_message,
    get_system_message,
)


class PrivacyPolicyExplainer:
    def __init__(self, privacy_policy: str) -> None:
        self.system_msg = get_system_message(privacy_policy=privacy_policy)
        self.model = ChatOpenAI(
            model=model_name,
            base_url=llm_url,
            api_key=GROQ_API_KEY,
        )

    def flash_summary(self) -> FlashSummaryOutput:
        parser = PydanticOutputParser(pydantic_object=FlashSummaryOutput)

        template = """Return a JSON object that matches this structure:
{format_instructions}

Question: {question}
        """

        prompt = ChatPromptTemplate.from_template(
            template,
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        messages = prompt.format_messages(question=get_flash_summary_message())
        response = self.model.invoke(messages)
        text = str(response.content)

        result = parser.parse(text)
        return result

    def ask_question(self, question: str) -> Iterator[BaseMessageChunk]:

        messages = [
            self.system_msg,
            HumanMessage(content=question)
        ]

        return self.model.stream(messages)
