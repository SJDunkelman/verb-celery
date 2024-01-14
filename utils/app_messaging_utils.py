from models.messaging.in_app_message import InAppMessage, MessageRole
from db import supabase_client
from utils.redis_utils import publish_message


def get_workflow_in_app_messages(workflow_id: str) -> list[InAppMessage]:
    in_app_message_results = supabase_client.table('in_app_message').select('created_at, user_id, message, role').eq('workflow_id', workflow_id).execute()
    in_app_messages = [InAppMessage(**message) for message in in_app_message_results.data]
    return in_app_messages


def send_message_to_user(workflow_id: str, message: str) -> InAppMessage:
    message_result = supabase_client.table('in_app_message').insert([{
        'workflow_id': workflow_id,
        'message': message,
        'role': MessageRole.assistant
    }]).execute()
    new_message = InAppMessage(**message_result.data[0])
    workflow_chat_channel = f"workflow:{workflow_id}:chat"
    publish_message(workflow_chat_channel, new_message.model_dump(mode='json'))
    return new_message
