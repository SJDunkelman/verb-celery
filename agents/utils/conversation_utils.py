import logging
from context.base_knowledge import BaseKnowledge
from typing import Type
from db import supabase_client
from models.messaging.agent_conversation import AgentConversation
from shared_enum.message_role import MessageRole
import json
from models.messaging.agent_conversation import AgentConversationMessage


def get_active_agent_conversation(workflow_id: str) -> AgentConversation | None:
    """
    Returns the agent conversation that is active for a workflow
    :param workflow_id:
    :return: (conversation_id, object_class_name) if active or None if no active conversation
    """
    conversation_result = supabase_client.table('agent_conversation').select('id, object_class_name, workflow_node_id').eq('workflow_id', workflow_id).eq('completed', False).execute()
    if len(conversation_result.data) > 1:
        logging.error(f"More than one conversation open for the workflow {workflow_id}")
        raise ValueError(f"More than one conversation open for the workflow {workflow_id}")
    elif len(conversation_result.data) == 0:
        return None
    return AgentConversation(
        id=int(conversation_result.data[0]['id']),
        workflow_node_id=conversation_result.data[0]['workflow_node_id'],
        object_class_name=conversation_result.data[0]['object_class_name']
    )


def save_agent_message(conversation_id: int,
                       message: str,
                       sent_by_user: bool = False,
                       extracted_model_data: dict | None = None):
    role = MessageRole.user if sent_by_user else MessageRole.assistant
    extracted_model = json.dumps(extracted_model_data) if extracted_model_data else None

    supabase_client.table('agent_conversation_message').insert({
        'message': message,
        'role': role,
        'conversation_id': conversation_id,
        'extracted_model_data': extracted_model
    }).execute()



def get_agent_conversation_messages(conversation_id: int, object_class: Type[BaseKnowledge]) -> list[AgentConversationMessage] | None:
    previous_message_results = supabase_client.table('agent_conversation_message').select('*').eq('conversation_id', conversation_id).order(
        'created_at', desc=False).execute()
    if previous_message_results.data:
        messages = []
        for msg in previous_message_results.data:
            if msg['extracted_model_data'] is not None:
                context_model = object_class.model_validate(json.loads(msg['extracted_model_data']))
            else:
                context_model = None
            messages.append(AgentConversationMessage(
                created_at=msg['created_at'],
                role=msg['role'],
                message=msg['message'],
                extracted_model=context_model
            ))
        return messages
    return None
