import logging
from celery import shared_task
from db import supabase_client
from utils.app_messaging_utils import send_message_to_user
from utils.redis_utils import publish_message
from postgrest.exceptions import APIError
from nlp_service.intent_parser import parse_message_intent, parse_message_pathway
from workflow.data_object import DataObject, Intent
import json


@shared_task(queue='messages_queue')
def process_user_message(workflow_id: str, input_workflow_node_id: str, user_id: str, message: str):
    # Save the incoming message to the database
    try:
        response = supabase_client.table('in_app_message').insert({
            'workflow_id': workflow_id,
            'user_id': user_id,
            'message': message
        }).execute()
        message_id = response.data[0]['id']
    except APIError:
        raise Exception('Failed to save message to database')

    # Load workflow data
    try:
        workflow_result = supabase_client.table("workflow").select("*").eq('id', workflow_id).single().execute()
        workflow_name = workflow_result.data['name']
    except APIError:
        raise Exception('Failed to load workflow data')

    try:
        workflow_pathway_results = supabase_client.table("workflow_pathway_details").select("*").eq('workflow_id',
                                                                                                    workflow_id).execute()
        workflow_pathways = [{
            'name': pathway['pathway_name'],
            'description': pathway['pathway_description']
        } for pathway in workflow_pathway_results.data]
    except APIError:
        raise Exception('Failed to load workflow pathway data')

    try:
        workflow_setting_results = supabase_client.table("workflow_setting_details").select("*").eq('workflow_id',
                                                                                                    workflow_id).execute()
        workflow_settings = [setting['setting_name'] for setting in workflow_setting_results.data]
    except APIError:
        raise Exception('Failed to load workflow settings data')

    try:
        workflow_node_results = supabase_client.rpc("get_all_workflow_node_details", params={'p_workflow_id': workflow_id}).execute()
        workflow_nodes = [{
            'name': node['name'],
            'description': node['description'],
            'base_type': node['base_type']
        } for node in workflow_node_results.data]
    except APIError:
        raise Exception('Failed to load workflow node data')

    # Parse the message to create a data object
    message_intent = parse_message_intent(message=message,
                                          title=workflow_name,
                                          nodes=workflow_nodes,
                                          settings=workflow_settings,
                                          pathways=workflow_pathways)
    logging.info(f'Parsed message intent: {message_intent}')

    try:
        intent = Intent(message_intent)
    except ValueError:
        raise Exception('Failed to parse message intent')

    if intent == Intent.COMPLETE:
        message_pathway = parse_message_pathway(message=message, pathways=workflow_pathways)
        pathway_id = None
        for pathway in workflow_pathway_results.data:
            if pathway['pathway_name'] == message_pathway:
                pathway_id = pathway['pathway_id']
                break
        if pathway_id is None:
            raise Exception('Failed to parse message pathway')
        data_object = DataObject.create_from_input_node(intent=Intent.COMPLETE,
                                                        input_node_id=input_workflow_node_id,
                                                        user_id=user_id,
                                                        pathway_id=pathway_id,
                                                        workflow_id=workflow_id)
        data_object.save()
        data_object_json = data_object.get_json
        data_object_dict = json.loads(data_object_json)
        publish_message(f'data_objects', data_object_dict)
        send_message_to_user(workflow_id=workflow_id,
                             message="Running the workflow now, please wait...")
        return data_object_json
