from enum import Enum
from typing import Any
from uuid import UUID
from db import supabase_client
from workflow.data_object import DataObject
from pydantic import BaseModel
import context as context_models
from utils.pydantic_utils import create_model_from_dict
from utils.pydantic_utils import create_model_instances_from_context_json
import json
import pathlib
import inspect


class NodeType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    PROCESS = "process"

    def __str__(self):
        return f"{self.value} node"


class Node:
    def __init__(self, workflow_node_id: UUID, context: dict[str, BaseModel] | None = None):
        self.workflow_node_id: UUID = workflow_node_id
        if context is None:
            context = {}
        self.context = context

    def execute(self, data_object: DataObject) -> Any:
        # Process method implementation
        raise NotImplementedError("Process method must be implemented in the derived class")

    def get_context_item(self, key: str, data_object: DataObject) -> Any:
        # Implement so does a merge in favour of the data_object context if present in data_object.context
        if key in data_object.context:
            item = data_object.context[key]
        else:
            item = self.context[key]

        if isinstance(item, dict):
            return create_model_from_dict(context_models, key, item)

    def add_context_item(self, context_model: BaseModel):
        self.context[context_model.__class__.__name__] = context_model

    def save_context(self):
        supabase_client.table('workflow_node_context').update({
            "context": json.dumps(self.context)
        }).eq('id', self.workflow_node_id).execute()

    def load_context(self):
        node_context_result = supabase_client.table('workflow_node_context').select('context').eq('node_id', self.workflow_node_id).order('timestamp', desc=True).limit(1).execute()
        if node_context_result.data:
            node_context_dict = json.loads(node_context_result.data[0]['context'])
            node_context = create_model_instances_from_context_json(context_models, node_context_dict)
            self.context = node_context
        else:
            self.context = {}

    def is_context_complete(self):
        context_item_results = supabase_client.rpc('get_context_items_for_workflow_node', {'input_workflow_node_id': self.workflow_node_id}).execute()
        needed_context_items = [item['context_item_class_name'] for item in context_item_results.data]
        if len(needed_context_items):
            missing_models = [class_name for class_name in needed_context_items if class_name not in self.context.keys()]
            return len(missing_models) == 0
        return True

    @classmethod
    def get_missing_context_items(cls, workflow_node_id: str, current_context: list[str]) -> list[str] | None:
        context_item_results = supabase_client.rpc('get_context_items_for_workflow_node', {'input_workflow_node_id': workflow_node_id}).execute()
        needed_context_items = [item['context_item_class_name'] for item in context_item_results.data]
        if len(needed_context_items):
            missing_models = [class_name for class_name in needed_context_items if class_name not in current_context]
            return missing_models
        return None

    @property
    def directory(self):
        # Get the file path of the current module and return parent directory
        module_path = inspect.getfile(self.__class__)
        return pathlib.Path(module_path).parent


class DataSourceNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def fetch_data(self, *args, **kwargs) -> Any:
        raise NotImplementedError("Fetch_data method must be implemented in the derived class")


class ProcessNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, data_object: DataObject) -> Any:
        # Implement processing logic here
        ...


class InputNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, data_object: DataObject) -> Any:
        # Process input data, if necessary
        ...


class OutputNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, data_object: DataObject) -> Any:
        ...

    def store_output(self, data: Any) -> None:
        pass
        # Implement logic to store or send the output data

