from enum import Enum
from models.data_object.metadata import Metadata
from shared_enum.data_object_status import DataObjectStatus
from db import supabase_client
from postgrest.exceptions import APIError
from utils.json_utils import CustomJSONEncoder
import json
from pydantic import BaseModel
import importlib
from datetime import datetime
from utils.merge_utils import combine_data_contents
import logging


class Intent(Enum):
    COMPLETE = 'COMPLETE'
    AMEND = 'AMEND'
    RETRIEVE = 'RETRIEVE'
    SAMPLE = 'SAMPLE'

    def __str__(self):
        return self.value


class DataObject:
    def __init__(self,
                 intent: Intent,
                 metadata: Metadata | dict,
                 data_object_id: str | None = None,
                 workflow_id: str | None = None,
                 pathway_id: str | None = None,
                 target_node_id: str | None = None,
                 context: dict[str, dict] | None = None):
        if isinstance(intent, str):
            try:
                intent = Intent(intent)
            except ValueError:
                raise Exception(f'Invalid intent: {intent}')
        self.intent = intent
        self.data_object_id = data_object_id
        if self.data_object_id:
            self.data_content = self.load_data_content(self.data_object_id)
        else:
            self.data_content = {}
        self.workflow_id = workflow_id

        if isinstance(metadata, dict):
            metadata = Metadata(**metadata)
        self.metadata = metadata

        if intent == Intent.COMPLETE:
            assert pathway_id is not None
        else:
            assert target_node_id is not None
        self.pathway_id = pathway_id
        self.target_node_id = target_node_id

        if context is None:
            context = {}
        self.context = context

    def save(self):
        data_object_dict = json.loads(self.get_json)
        data_object_dict.pop('workflow_id', None)
        data_object_dict.pop('data_object_id', None)
        try:
            if self.data_object_id:
                supabase_client.table('data_object').update(data_object_dict).eq('id', self.data_object_id).execute()
            else:
                response = supabase_client.table('data_object').insert(data_object_dict).execute()
                self.data_object_id = response.data[0]['id']
        except APIError:
            raise Exception('Failed to update data object in database')

    def add_context_item_pydantic(self, context_model: BaseModel):
        context_model_dict = context_model.model_dump()
        context_model_name = context_model.__class__.__name__
        self.context[context_model_name] = context_model_dict

    def load_context_items(self):
        for key, value in self.context.items():
            context_module = importlib.import_module('core.context')
            context_class = getattr(context_module, value['model'])
            # Replace the context item value with the dynamically imported Pydantic model instance
            self.context[key] = context_class(**value['data'])

    def move_to_next_node(self,
                          next_workflow_node_id: str,
                          new_status: DataObjectStatus = DataObjectStatus.IN_PROGRESS,
                          modifying_user_id: str | None = None):
        self.metadata.update(previous_node_status=self.metadata.current_status)
        self.metadata.update(previous_workflow_node_id=self.metadata.current_workflow_node_id)
        self.metadata.update(current_workflow_node_id=next_workflow_node_id)
        self.metadata.update(current_status=new_status)
        if modifying_user_id:
            self.metadata.update(last_modified_by_user_id=modifying_user_id)
        self.metadata.update(last_modified_at=datetime.utcnow())
        self.save()

    def store_transition(self, from_node_id: str, to_node_id: str, new_data_content: dict):
        """Stores the transition along with the new data content."""
        try:
            transition_entry = {
                'from_node_id': from_node_id,
                'to_node_id': to_node_id,
                'new_data_content': json.dumps(new_data_content, cls=CustomJSONEncoder),
                'data_object_id': self.data_object_id
            }
            result = supabase_client.table('data_object_transition').insert(transition_entry).execute()
            return result.data
        except APIError as e:
            logging.error(f'Failed to store data object transition: {e}')
            raise e

    def update_context(self, context_key: str, context_value: dict):
        """Updates the context of the data object, possibly with new information from the user."""
        if context_key not in self.context:
            self.context[context_key] = context_value
        else:
            self.context[context_key].update(context_value)
        self.save()

    @classmethod
    def load_data_content(cls, data_object_id: str):
        try:
            data_content_results = supabase_client.table('data_object_transition').select(
                'created_at, new_data_content').eq('data_object_id', data_object_id).execute()
        except APIError:
            raise Exception('Failed to load data content')
        sorted_transitions = sorted(data_content_results.data, key=lambda x: x['created_at'])
        final_data_content = {}
        for transition in sorted_transitions:
            new_data_content = transition['new_data_content']
            if isinstance(new_data_content, str):
                new_data_content = json.loads(new_data_content)
            if new_data_content:
                final_data_content = combine_data_contents(final_data_content, new_data_content)
        return final_data_content

    @classmethod
    def create_from_input_node(cls, intent: Intent, input_node_id: str, user_id: str, **kwargs):
        new_metadata = Metadata(
            created_by_user_id=user_id,
            last_modified_by_user_id=user_id,
            current_status=DataObjectStatus.COMPLETED,
            current_workflow_node_id=input_node_id
        )

        if 'workflow_id' in kwargs:
            workflow_id = kwargs['workflow_id']
        else:
            workflow_id = None

        if intent == Intent.COMPLETE:
            assert 'pathway_id' in kwargs, 'Pathway ID must be provided for COMPLETE intent'
            return cls(intent=intent, metadata=new_metadata, pathway_id=kwargs['pathway_id'], workflow_id=workflow_id)
        else:
            assert 'target_node_id' in kwargs, 'Target node ID must be provided for AMEND, RETRIEVE, and SAMPLE intents'
            return cls(intent=intent, metadata=new_metadata, target_node_id=kwargs['target_node_id'],
                       workflow_id=workflow_id)

    @classmethod
    def create_from_dict(cls, data_object_dict: dict):
        metadata_fields = list(Metadata.model_fields.keys())
        metadata_dict = {field: data_object_dict[field] for field in metadata_fields if field in data_object_dict}
        metadata = Metadata(**metadata_dict)
        return cls(
            intent=data_object_dict['intent'],
            metadata=metadata,
            data_object_id=data_object_dict.get('data_object_id', None),
            workflow_id=data_object_dict.get('workflow_id', None),
            pathway_id=data_object_dict.get('pathway_id'),
            target_node_id=data_object_dict.get('target_node_id'),
            context=data_object_dict.get('context', {})
        )

    @property
    def get_dict(self):
        return json.loads(self.get_json)

    @property
    def get_json(self):
        data_object_dict = self.metadata.model_dump()
        data_object_dict.update({
            'intent': str(self.intent),
            'pathway_id': self.pathway_id,
            'target_node_id': self.target_node_id,
            'context': self.context
        })
        if self.data_object_id:
            data_object_dict['data_object_id'] = self.data_object_id
        if self.workflow_id:
            data_object_dict['workflow_id'] = self.workflow_id
        json_data = json.dumps(data_object_dict, cls=CustomJSONEncoder)
        return json_data


# Usage example, assuming a Pydantic model named ExampleModel is defined in core.models.data_objects
data_object = DataObject.create_from_input_node(intent=Intent.COMPLETE,
                                                input_node_id="62817448-458c-4c3d-a2e8-5f8ce6606b7f",
                                                user_id="249bb8f0-2c31-48c0-ac05-37059f638dc2",
                                                pathway_id="bde58f5c-8004-40db-9cf3-4d80d18d58f1")
# data_object.save()
