from context.base_knowledge import BaseKnowledge
from typing import Type
from context import available_context_items


def get_context_model_class(model_name: str) -> Type[BaseKnowledge]:
    context_class = available_context_items.get(model_name)
    if not context_class:
        raise ValueError(f"No plugin class found for {model_name}")
    return context_class


def create_context_model_from_dict(model_name: str, model_data: dict) -> BaseKnowledge:
    context_class = get_context_model_class(model_name)
    return context_class.model_validate(model_data)
