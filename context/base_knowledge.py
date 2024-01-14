from pydantic import BaseModel
from typing import Union, get_args, get_origin
import types
import json


class BaseKnowledge(BaseModel):
    def user_representation(self) -> str:
        description = ""
        for field_name, value in self.__dict__.items():
            if value is not None:
                field_name = f"**{field_name.replace('_', ' ').title()}**"
                description += f"- {field_name}: {value}\n"
        return description

    @property
    def json_representation(self) -> str:
        return json.dumps(self.model_dump(), indent=4)

    @classmethod
    def string_representation(cls):
        description = f"{cls.__name__} Model:\n"
        for field_name, field_type in cls.__annotations__.items():
            # Fetch field description if available
            field_info = cls.model_fields.get(field_name)
            field_desc = field_info.description if field_info and field_info.description else ""

            # Make pipe-separated list of type names if multiple for attribute
            if get_origin(field_type) is Union or isinstance(field_type, types.UnionType):
                union_types = get_args(field_type)
                type_names = ' | '.join([t.__name__ for t in union_types if hasattr(t, '__name__')])
            else:
                type_names = field_type.__name__

            description += f"- {field_name} (Type {type_names})"
            if field_desc:
                description += f": {field_desc}"
            description += "\n"
        return description

    @classmethod
    def initial_message(cls):
        raise NotImplementedError("initial_message property must be implemented in the derived class")

    @classmethod
    def confirmation_message(cls):
        raise NotImplementedError("confirmation_message property must be implemented in the derived class")
