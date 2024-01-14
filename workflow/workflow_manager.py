from tasks.message_parsing import process_user_message
from tasks.execute_node import execute_node
from tasks.agent_conversation import converse_with_context_extraction_agent, initiate_agent_conversation
from utils.redis_utils import subscribe_to_channel, publish_message
from utils.app_messaging_utils import send_message_to_user
from workflow.data_object import DataObject
from agents.utils.conversation_utils import get_active_agent_conversation
from workflow.data_object import Intent
from workflow.pathway import WorkflowPathway
from db import supabase_client
import json
from threading import Thread
import logging
from shared_enum.workflow_stage import WorkflowStage


class WorkflowManager:
    def __init__(self):
        self.messages_pubsub_channel = subscribe_to_channel(f'messages')
        self.data_objects_pubsub_channel = subscribe_to_channel('data_objects')
        self.workflow_node_ready_channel = subscribe_to_channel('workflow_node_ready')

    def listen_for_messages(self):
        while True:
            message = self.messages_pubsub_channel.get_message()
            if message and message.get('type') == 'message':
                logging.info(message)
                try:
                    message_data = json.loads(message['data'])
                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError encountered: {e}")
                    continue

                """
                If agent conversation is active (found by checking if stage of workflow is CONVERSING), send message to agent conversation queue
                """
                # Check if agent conversation is active
                active_agent_conversation = get_active_agent_conversation(message_data['workflow_id'])
                if active_agent_conversation is not None:
                    logging.info("Agent conversation is active, sending message to agent conversation queue")
                    message_task = converse_with_context_extraction_agent.delay(
                        agent_conversation_id=active_agent_conversation.id,
                        missing_object_class_name=active_agent_conversation.object_class_name,
                        workflow_id=message_data['workflow_id'],
                        workflow_node_id=active_agent_conversation.workflow_node_id,
                        user_message=message_data['message'])
                else:
                    # Enqueue processing of the message
                    message_task = process_user_message.delay(workflow_id=message_data['workflow_id'],
                                                              input_workflow_node_id=message_data['input_workflow_node_id'],
                                                              user_id=message_data['user_id'],
                                                              message=message_data['message'])

                # logging.info(f"Result type before calling get(): {type(user_message_task)}")
                # Send message
                # send_message_to_user(message_data['workflow_id'], "This is a response")

                try:
                    task_result = message_task.get(timeout=20)  # Waits for 20 seconds for the task to complete
                except TimeoutError:
                    logging.error(f"Task did not complete in 20 seconds: {message_task.id}")

                # Send a message based on the intent of the message
                # if message_intent == Intent.COMPLETE:

    def listen_for_data_objects(self):
        while True:
            message = self.data_objects_pubsub_channel.get_message()
            if message and message.get('type') == 'message':
                logging.info(message)
                data_object_dict = json.loads(message['data'])
                workflow_id = data_object_dict['workflow_id']
                # logic to retrieve node from db and enqueue node processing here
                # Move data object to next node
                data_object = DataObject.create_from_dict(data_object_dict)

                match data_object.intent:
                    case Intent.COMPLETE:
                        # Get workflow pathway and move node to next node
                        workflow_pathway = WorkflowPathway(workflow_id=workflow_id,
                                                           pathway_id=data_object.pathway_id)
                        workflow_pathway.load_pathway_nodes()
                        next_workflow_node = workflow_pathway.get_next_node(
                            data_object.metadata.current_workflow_node_id)
                        next_workflow_node_id = next_workflow_node['workflow_node_id']
                        data_object.move_to_next_node(next_workflow_node_id)

                        # TODO: Create Pydantic models from additional data object context and add to data object

                        # Enqueue execution of the next node
                        result = execute_node.delay(workflow_id=workflow_id,
                                                    workflow_node_id=str(data_object.metadata.current_workflow_node_id),
                                                    data_object_dict=data_object.get_dict)
                        send_message_to_user(workflow_id=data_object.workflow_id,
                                             message=f"{next_workflow_node['base_type']} NODE: {next_workflow_node['class_name']} started!")
                        try:
                            task_result = result.get(timeout=10)  # Or whatever timeout makes sense

                            if task_result['success']:
                                pass
                            else:
                                if task_result['error'] == "ContextMissingError":
                                    missing_items = task_result['missing_items']
                                    logging.info(f"Context missing error encountered, initiating agent conversation: {missing_items}")
                                    initiate_agent_task = initiate_agent_conversation.delay(
                                        workflow_id=workflow_id,
                                        workflow_node_id=str(data_object.metadata.current_workflow_node_id),
                                        missing_context_item=missing_items[0])
                        except TimeoutError:
                            logging.error(f"Task did not complete in 10 seconds: {result.id}")
                        except Exception as e:
                            logging.error(e)
                        # except ContextMissingError as e:
                        #     # missing_items = e.missing_context_class_names
                        #     logging.info("Context missing error encountered, initiating agent conversation")
                        #     # logging.info(f"\n\nMissing items: {missing_items}\n\n")
                        #     initiate_agent_task = initiate_agent_conversation.delay(
                        #         workflow_id=workflow_id,
                        #         workflow_node_id=data_object.metadata.current_workflow_node_id,
                        #         missing_context_item=e.missing_context_class_names[0])
                        # except Exception as e:
                        #     # Handle other exceptions
                        #     pass

    def listen_for_workflow_node_ready(self):
        while True:
            message = self.workflow_node_ready_channel.get_message()
            if message and message.get('type') == 'message':
                logging.info(message)
                message_data = json.loads(message['data'])
                # self.execute_workflow_node(message_data['workflow_id'], message_data['workflow_node_id'])
                data_object_result = supabase_client.table('data_object').select('*').eq('id', message_data['data_object_id']).single().execute()
                data_object = DataObject.create_from_dict(data_object_result.data)

                # Trigger node execution with the correct DataObject
                execute_node.delay(
                    workflow_id=message_data['workflow_id'],
                    workflow_node_id=message_data['workflow_node_id'],
                    data_object_dict=data_object.get_dict()
                )

    def start(self):
        Thread(target=self.listen_for_messages, daemon=True).start()
        Thread(target=self.listen_for_data_objects, daemon=True).start()
        Thread(target=self.listen_for_workflow_node_ready, daemon=True).start()

    # ...additional methods for starting, pausing and resuming workflows


"""
Refactor:

    def listen(self, channel_name, handler):
        pubsub_channel = subscribe_to_channel(channel_name)
        while True:
            message = pubsub_channel.get_message()
            if message and message.get('type') == 'message':
                try:
                    message_data = json.loads(message['data'])
                    handler(message_data)
                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError encountered: {e}")
                    
    def start(self):
        Thread(target=lambda: self.listen('messages', self.process_workflow_message), daemon=True).start()
        Thread(target=lambda: self.listen('data_objects', self.process_data_objects_messages), daemon=True).start()
    
    Define:
    process_workflow_message
    process_data_objects_messages
"""
