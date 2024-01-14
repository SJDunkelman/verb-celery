from celery import shared_task
from db import supabase_client
from utils.pydantic_utils import create_model_instances_from_context_json
import context as context_models
from workflow.data_object import DataObject
from workflow.node import Node
from plugins.factory import get_node_class
from utils.merge_utils import combine_data_contents


@shared_task(queue='node_processing_queue')
def execute_node(workflow_id: str, workflow_node_id: str, data_object_dict: dict):
    data_object = DataObject.create_from_dict(data_object_dict)

    # Create instance of node
    node_details_result = supabase_client.rpc('get_workflow_node_details',
                                              {'workflow_node_id': str(workflow_node_id)}).execute()
    node_class = get_node_class(node_details_result.data[0]['class_name'])

    # Load node context
    node_context_result = supabase_client.table('workflow_node_context').select('context'). \
        eq('workflow_node_id', str(workflow_node_id)).order('timestamp', desc=True).limit(1).execute()

    if node_context_result.data:
        node_context_dict = node_context_result.data[0]['context']
        node_context = create_model_instances_from_context_json(context_models, node_context_dict)
    else:
        node_context = {}

    # Check if node context + data object context satisfies all node context requirements
    data_object_context = data_object.context
    merged_context = combine_data_contents(older=node_context, newer=data_object_context)
    missing_context_class_names = Node.get_missing_context_items(workflow_node_id=str(workflow_node_id),
                                                                 current_context=list(merged_context.keys()))
    if missing_context_class_names:
        # If not complete, initiate agent conversation
        return {"success": False, "error": "ContextMissingError", "missing_items": missing_context_class_names}
        # raise ContextMissingError(f"Missing context items for node: {str(workflow_node_id)}", missing_context_class_names)

    # If complete, load data object data content
    node = node_class(workflow_node_id=workflow_node_id, context=merged_context)
    node_output = node.execute(data_object)
    transition_data = data_object.store_transition(
        from_node_id=data_object.metadata.previous_workflow_node_id,
        to_node_id=workflow_node_id,
        new_data_content=node_output
    )
    if transition_data:
        # Pass data_object_dict to the next node or complete the workflow.
        return {"success": True, "data_object_dict": data_object.get_dict()}
    else:
        return {"success": False, "error": "DataTransitionError"}
