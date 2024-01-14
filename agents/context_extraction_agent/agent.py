from agents.base_agent import BaseAgent
from context.base_knowledge import BaseKnowledge
from ai import mixtral_ai, gpt4_ai, fuser, fsystem
import json
from typing import Type
import logging


class ContextExtractionAgent(BaseAgent):
    def extract_context_model_from_message(self, message: str, context_model_class: Type[BaseKnowledge]) -> BaseKnowledge:
        instruct_prompt = open(self.prompts_directory / "extract_model_instruct").read()

        context = f"{context_model_class.string_representation()}\n\nMessage: {message}"
        response = gpt4_ai.chat_completion(
            messages=[fsystem(instruct_prompt), fuser(context)],
            temperature=0.5
        )
        try:
            model_json = json.loads(response)
            extracted_model = context_model_class(**model_json)
            return extracted_model
        except:
            logging.error(f"Could not extract context model from message: {message}")
            raise ValueError(f"Could not extract context model from message: {message}")

    def amend_context_model_from_message(self, message: str, context_model: BaseKnowledge) -> BaseKnowledge:
        instruct_prompt = open(self.prompts_directory / "amend_model_instruct").read()
        context = (f"{context_model.string_representation()}\n\n"
                   f"Current model instance JSON:{context_model.json_representation}\n\nFeedback: {message}"
                   )
        response = gpt4_ai.chat_completion(
            messages=[fsystem(instruct_prompt), fuser(context)],
            temperature=0.5
        )
        model_json = json.loads(response)
        context_model_class = type(context_model)
        return context_model_class(**model_json)

    def classify_if_message_acceptance(self, message: str) -> bool:
        instruct_prompt = open(self.prompts_directory / "classify_message_acceptance_instruct").read()
        classification_response = mixtral_ai.chat_completion(
            messages=[fsystem(instruct_prompt), fuser(message)],
            max_tokens=3,
            temperature=0.2
        )
        return classification_response.strip() == 'ACCEPT'


# if __name__ == "__main__":
#     from core import context
#     c = ContextExtractionAgent()
#     instruct_prompt = open(c.prompts_directory / "extract_model_instruct").read()
#     context_model_class = context.TargetCustomer
#     message = "I want to target sales leaders at Microsoft in the bay area"
#     new_model = c.extract_context_model_from_message(message, context_model_class)
#     print(new_model.json_representation)
#
#     feedback = "Change to all Big Tech in London"
#     amended_model = c.amend_context_model_from_message(feedback, new_model)
#     print(amended_model.json_representation)
