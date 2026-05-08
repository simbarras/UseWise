import logging

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from openai import RateLimitError

from usewise.llm.config import fallback_model_name, get_groq_api_key, llm_url
from usewise.llm.risk import ANSWER_KEYS, calculate_risk
from usewise.llm.schemas import (
    CombinedSummaryLLMOutput,
    FlashSummary,
    FlashSummaryAnswer,
    FlashSummaryReturnType,
    get_combined_summary_message,
    get_json_prompt_template,
    get_system_message,
)

logger = logging.getLogger(__name__)


class PrivacyPolicyExplainer:
    def __init__(self, privacy_policy: str, model_name: str) -> None:
        self.privacy_policy = privacy_policy
        self.system_msg = get_system_message()
        self.messages: list[BaseMessage] = [self.system_msg]
        self.model = ChatOpenAI(
            model=model_name,
            base_url=llm_url,
            api_key=get_groq_api_key(),
        )
        self.fallback_model = ChatOpenAI(
            model=fallback_model_name,
            base_url=llm_url,
            api_key=get_groq_api_key(),
        )


    def get_combined_summary(
        self,
        questions: list[tuple[str, FlashSummaryReturnType]],
        follow_up_questions: list[str],
    ) -> tuple[FlashSummary, list[str]]:
        parser = PydanticOutputParser(pydantic_object=CombinedSummaryLLMOutput)
        prompt_messages = self._get_prompt(parser, questions, follow_up_questions)
        messages: list[BaseMessage] = [self.system_msg, *prompt_messages]
        response = self._get_response(messages)
        flash_summary, follow_up_answers = self._format_answer(
            parser, response, questions
        )
        return flash_summary, follow_up_answers

    def _get_prompt(
        self,
        parser: PydanticOutputParser[CombinedSummaryLLMOutput],
        questions: list[tuple[str, FlashSummaryReturnType]],
        follow_up_questions: list[str],
    ) -> list[BaseMessage]:
        yes_no_questions, time_based_questions = self.divide_questions(questions)
        prompt = get_json_prompt_template(parser)
        question = get_combined_summary_message(
            self.privacy_policy, yes_no_questions,
              time_based_questions, follow_up_questions
        )
        return prompt.format_messages(question=question)

    def _get_response(self, messages: list[BaseMessage]) -> BaseMessage:
        try:
            response = self.model.invoke(messages)
        except RateLimitError:
            logger.warning(
                "Rate limit hit with %s,"
                " falling back to %s",
                self.model.model_name,
                fallback_model_name
            )
            response = self.fallback_model.invoke(messages)

        return response


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

    def _format_answer(
        self,
        parser: PydanticOutputParser[CombinedSummaryLLMOutput],
        response: BaseMessage,
        questions: list[tuple[str, FlashSummaryReturnType]],
    ) -> tuple[FlashSummary, list[str]]:
        text = str(response.content)
        text_parsed = parser.parse(text)
        answers = self.reassemble_questions(
            text_parsed.flags, text_parsed.times, questions
        )
        answers_dict = {
            key: a.value for key, a in zip(ANSWER_KEYS, answers, strict=True)
        }
        score = calculate_risk(answers_dict)
        flash_summary = FlashSummary(answers=answers, score=score)
        self.messages.append(
            AIMessage(
                content=self._format_flash_summary_memory(questions, flash_summary)
            )
        )
        return flash_summary, text_parsed.follow_up_answers

    def reassemble_questions(
        self,
        flags: list[bool | None],
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

    def _format_flash_summary_memory(
        self,
        questions: list[tuple[str, FlashSummaryReturnType]],
        flash_summary: FlashSummary,
    ) -> str:
        summary_lines = [
            "Flash summary previously generated for this privacy policy:",
        ]

        for (question, _), answer in zip(questions, flash_summary.answers, strict=False):
            summary_lines.append(f"- {question}: {answer.value}")

        summary_lines.append(f"- Privacy risk score: {flash_summary.score}/10")
        return "\n".join(summary_lines)
