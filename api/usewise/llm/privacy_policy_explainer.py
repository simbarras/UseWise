from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from usewise.llm.config import get_groq_api_key, llm_url
from usewise.llm.schemas import (
    FlashSummary,
    FlashSummaryAnswer,
    FlashSummaryLLMOutput,
    FlashSummaryReturnType,
    get_flash_summary_message,
    get_json_prompt_template,
    get_system_message,
)


class PrivacyPolicyExplainer:
    def __init__(self, privacy_policy: str, model_name: str) -> None:
        self.system_msg = get_system_message(privacy_policy=privacy_policy)
        self.model = ChatOpenAI(
            model=model_name,
            base_url=llm_url,
            api_key=get_groq_api_key(),
        )

    def get_flash_summary(
        self, questions: list[tuple[str, FlashSummaryReturnType]]
    ) -> FlashSummary:
        yes_no_questions, time_based_questions = self.divide_questions(questions)
        parser = PydanticOutputParser(pydantic_object=FlashSummaryLLMOutput)
        prompt = get_json_prompt_template(parser)
        question = get_flash_summary_message(yes_no_questions, time_based_questions)
        messages = prompt.format_messages(question=question)
        response = self.model.invoke(messages)
        text = str(response.content)
        text_parsed = parser.parse(text)
        answers = self.reassemble_questions(
            text_parsed.flags, text_parsed.times, questions
        )
        return FlashSummary(answers=answers, score=text_parsed.score)

    def divide_questions(
        self, questions: list[tuple[str, FlashSummaryReturnType]]
    ) -> tuple[list[str], list[str]]:
        yes_no_questions = []
        time_based_questions = []
        flag = FlashSummaryReturnType.FLAG
        time = FlashSummaryReturnType.TIME
        for q, return_type in questions:
            if return_type == flag:
                yes_no_questions.append(q)
            elif return_type == time:
                time_based_questions.append(q)
            else:
                raise TypeError

        return yes_no_questions, time_based_questions

    def reassemble_questions(
        self,
        flags: list[bool],
        times: list[str],
        questions: list[tuple[str, FlashSummaryReturnType]],
    ) -> list[FlashSummaryAnswer]:
        answers: list[FlashSummaryAnswer] = []

        flag = FlashSummaryReturnType.FLAG
        time = FlashSummaryReturnType.TIME

        yes_iter = iter(flags)
        time_iter = iter(times)

        for _, return_type in questions:
            if return_type is flag:
                answers.append(FlashSummaryAnswer(value=next(yes_iter), type=return_type))
            elif return_type is time:
                answers.append(
                    FlashSummaryAnswer(value=next(time_iter), type=return_type)
                )
            else:
                raise TypeError

        return answers

    def get_questions_answers(self, questions: list[str]) -> list[str]:
        return [self.invoke(q) for q in questions]

    def invoke(self, question: str) -> str:

        messages = [self.system_msg, HumanMessage(content=question)]

        return str(self.model.invoke(messages).content)
