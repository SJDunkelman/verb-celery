from celery import shared_task
from db import supabase_client
from utils.app_messaging_utils import send_message_to_user
from agents.utils.conversation_utils import save_agent_message, get_agent_conversation_messages
from agents.context_extraction_agent.agent import ContextExtractionAgent
from plugins.factory import get_node_class
from context.factory import get_context_model_class
from shared_enum.workflow_stage import WorkflowStage
from utils.redis_utils import publish_message
import logging


@shared_task(queue='agent_conversation_queue')
def initiate_agent_conversation(workflow_id: str, workflow_node_id: str, missing_context_item: str):
    new_conversation_result = supabase_client.table('agent_conversation').insert({
        'workflow_id': workflow_id,
        'workflow_node_id': str(workflow_node_id),
        'object_class_name': missing_context_item
    }).execute()
    supabase_client.table('workflow').update({'stage': WorkflowStage.CONVERSING}).eq('id', workflow_id).execute()

    missing_context_item_class = get_context_model_class(missing_context_item)
    initial_message = missing_context_item_class.initial_message()
    send_message_to_user(workflow_id, str(initial_message))
    return {"success": True, "conversation_id": new_conversation_result.data[0]['id']}


@shared_task(queue='agent_conversation_queue')
def converse_with_context_extraction_agent(agent_conversation_id: int,
                                           missing_object_class_name: str,
                                           workflow_id: str,
                                           workflow_node_id: str,
                                           user_message: str):
    # Save user message
    save_agent_message(conversation_id=agent_conversation_id,
                       message=user_message,
                       sent_by_user=True)

    # Get agent conversation history
    missing_context_item_class = get_context_model_class(missing_object_class_name)
    previous_agent_messages = get_agent_conversation_messages(agent_conversation_id, missing_context_item_class)
    if previous_agent_messages:
        last_model_extracted = previous_agent_messages[-1].extracted_model
        logging.info("Last model extracted: {last_model_extracted}")
    else:
        last_model_extracted = None

    agent = ContextExtractionAgent()
    if last_model_extracted:
        logging.info(f"Last model extracted: {last_model_extracted}")
        is_acceptance = agent.classify_if_message_acceptance(user_message)
        if is_acceptance:
            # Update node context
            workflow_node_class_name = supabase_client.rpc('get_workflow_node_details', {"workflow_node_id": workflow_node_id}).execute().data[0]['class_name']
            node_class = get_node_class(workflow_node_class_name)
            node = node_class(workflow_node_id=workflow_node_id)
            node.load_context()
            node.add_context_item(last_model_extracted)
            node.save_context()

            data_object_result = supabase_client.table('agent_conversation').select('data_object_id').eq('id', agent_conversation_id).execute()
            data_object_id = data_object_result.data[0]['data_object_id']
            supabase_client.table('agent_conversation').update({'completed': True}).eq('id', agent_conversation_id).execute()

            publish_message('workflow_node_ready', {
                'workflow_id': workflow_id,
                'workflow_node_id': workflow_node_id,
                'data_object_id': data_object_id
            })

            # Send user back to user
            send_message_to_user(workflow_node_id, f"Thanks, I'll continue with the workflow now.")
            return {"success": True}
        else:
            # Update model with user response
            updated_model = agent.amend_context_model_from_message(user_message, last_model_extracted)
            # Send updated model and ask for confirmation or feedback
            extracted_model_response = "\n\n".join([updated_model.confirmation_message,
                                                    updated_model.user_representation()])
            send_message_to_user(workflow_node_id, extracted_model_response)
            save_agent_message(conversation_id=agent_conversation_id,
                               message=user_message,
                               sent_by_user=False,
                               extracted_model_data=updated_model.model_dump(mode='json'))
            return {"success": False}

    # try:
    extracted_model = agent.extract_context_model_from_message(user_message, missing_context_item_class)
    logging.info(f"Extracted model: {extracted_model}")
    # except ValueError:
    #     send_message_to_user(workflow_id, "Sorry, I couldn't understand that. Please try again.")
    #     return {"success": False}
    extracted_model_response = "\n\n".join([extracted_model.confirmation_message(),
                                            extracted_model.user_representation()])
    send_message_to_user(workflow_id, extracted_model_response)
    save_agent_message(conversation_id=agent_conversation_id,
                       message=user_message,
                       sent_by_user=False,
                       extracted_model_data=extracted_model.model_dump(mode='json'))
    return {"success": False}

    # If not first user response, check if a previous message in the conversation has a context item model
    # Analyse whether the user response is acceptance or amendment
    # Get the previous version of the extracted context item model
    # If amendment
    # Update the model with the user response
    # If acceptance
    # Update node context

    # If previous messages do not have context model
    # Extract model from message

    # Send updated model and ask for confirmation or feedback

    # If response couldn't be processed, ask for more details
