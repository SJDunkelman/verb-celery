import json
from pydantic import BaseModel, ValidationError
import logging
from typing import Type
from context.base_knowledge import BaseKnowledge


def get_model_class(pydantic_models_module, model_name: str) -> Type[BaseModel]:
    return getattr(pydantic_models_module, model_name, None)


def create_model_from_dict(pydantic_models_module, model_name: str, model_data: dict) -> BaseModel | BaseKnowledge:
    model_class = get_model_class(pydantic_models_module, model_name)
    if isinstance(model_class, type) and issubclass(model_class, BaseModel):
        return model_class.model_validate(model_data)


def create_model_instances_from_context_json(pydantic_models_module, json_str: str) -> dict[str, BaseModel]:
    """
    Dynamically create instances of Pydantic models from a JSON string.

    :param pydantic_models_module: The module containing Pydantic model classes.
    :param json_str: A JSON string with model names as keys and their data as values.
    :return: A dictionary of model instances keyed by the model names.
    """
    models_dict = json.loads(json_str)
    model_instances = {}

    for model_name, model_data in models_dict.items():
        # Dynamically get the model class from the module
        model_class = getattr(pydantic_models_module, model_name, None)

        # Check if the class is a Pydantic model and create an instance
        if isinstance(model_class, type) and issubclass(model_class, BaseModel):
            model_instance = model_class.model_validate(model_data)
            model_instances[model_name] = model_instance

    return model_instances


def parse_model_instance_from_llm_response(model_class: BaseModel, response: str) -> BaseModel:
    """
    Parse a model instance from a response from the Language Learning Model.

    :param model_class: The Pydantic model class to parse.
    :param response: The response from the LLM that follows the pattern of KEY = VALUE.
    :return: The parsed model instance.
    """
    string = response.replace('"', '')
    data = {}
    for line in string.split('\n'):
        try:
            key, value = line.split(' = ')
        except ValueError:
            # This happens when the line is the LLM bullshitting about (explaining, apologising etc.)
            continue
        key = key.lower()
        if value.upper() == "NONE":
            data[key] = None
            continue
        data[key] = value

    try:
        model_instance = model_class.model_validate(**data)
        return model_instance
    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        raise e
