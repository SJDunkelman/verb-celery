# import logging
# from celery import shared_task
# from core.db import supabase_client
# from core.utils.pydantic_utils import create_model_instances_from_context_json
# from core import node_data as node_data_models
# from core import context as context_models
# from postgrest.exceptions import APIError
# from core.workflow.data_object import DataObject
# import json
#
#
# @shared_task(queue='node_processing_queue')
# def process_node(workflow_node_id: str, data_object_id: str):
#     # Get data object context using supabase query
#     try:
#         context_result = supabase_client.table('data_object').select('context').eq('id', data_object_id).execute()
#         data_object_context_dict = json.loads(context_result['data'][0]['context'])
#     except APIError as e:
#         logging.error(f"Could not get data object context: {e}")
#         raise Exception("Could not get data object context")
#
#     try:
#         data_object_context = create_model_instances_from_context_json(context_models, json.dumps(data_object_context_dict))
#     except Exception as e:
#         logging.error(f"Could not create data object context: {e}")
#         raise Exception("Could not create data object context")
#
#     # Get data object data content using DataObject class method
#     try:
#         data_content_dict = DataObject.load_data_content(data_object_id)
#         data_content = create_model_instances_from_context_json(node_data_models, json.dumps(data_content_dict))
#     except Exception as e:
#         logging.error(f"Could not get data object data content: {e}")
#         raise Exception("Could not get data object data content")
#
#     # Get node context using supabase query
#
#     # try:
#     #     node_context_result = supabase_client.table('workflow_node_context').select('context').eq('node_id', workflow_node_id).order('timestamp', desc=True).limit(1).execute()
#     #     node_context_dict = json.loads(node_context_result.data[0]['context'])
#     #     node_context = create_model_instances_from_context_json(context_models, node_context_dict)
#     # except APIError as e:
#     #     logging.error(f"Could not get node context: {e}")
#     #     raise Exception("Could not get node context")
#
#     # Check that all node context items are valid by creating the pydantic models
#     # if not node.is_context_complete():
#     #     raise context missing exception
#
#     # Execute node
#     try:
#
#         result = node.execute(data_content)
#     except Exception as e:
#         logging.error(f"Could not execute node: {e}")
#         raise Exception("Could not execute node")
#
#     # Save node context
#
