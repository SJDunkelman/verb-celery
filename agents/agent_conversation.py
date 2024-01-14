# from typing import Type
# from pydantic import BaseModel
# from core.utils.llm_service import llm_extract_attributes, llm_amend_attributes
# from core.utils.messaging import send_message
#
#
# # Utility function that starts an agent conversation
# def start_agent_conversation(user_id: str, channel_info: dict, context_model: Type[BaseModel], message: str):
#     # Step 1: Send initial message
#     send_message(user_id, channel_info, f"Please describe your {context_model.__name__.lower()}")
#
#
# # Utility function to process user responses during an agent conversation
# def process_agent_response(user_id: str,
#                            channel_info: dict,
#                            context_model: Type[BaseModel],
#                            response: str,
#                            data_object_id: str):
#     # Step 2 & 3: LLM processes user response
#     extraction_result = llm_extract_attributes(response, context_model)
#     if extraction_result == "unsure":
#         # Ask the user to try again with suggestions
#         send_message(user_id, channel_info,
#                      f"Could not extract details correctly. Please describe your {context_model.__name__.lower()} in more detail.")
#     else:
#         # Step 4: Send extracted details
#         context_instance = context_model.parse_obj(extraction_result)
#         send_message(user_id, channel_info, str(context_instance) + "\nIs this information correct?")
#
#
# # Utility function that checks if user response is an acceptance or amendment
# def process_confirmation(user_id: str, channel_info: dict, context_model: Type[BaseModel], confirmation_response: str,
#                          current_model_data: dict, data_object_id: str):
#     is_acceptance = check_user_response(confirmation_response)  # Implement this to classify the response
#     if is_acceptance:
#         # Update the node's context with the new data and end conversation
#         update_node_context(data_object_id, current_model_data)
#         # Resume processing the node
#         process_node.delay(target_node_id, data_object_id)
#     else:
#         # Step 5: Process amendment and update the model
#         updated_model_data = llm_amend_attributes(current_model_data, confirmation_response, context_model)
#         process_agent_response(user_id, channel_info, context_model, updated_model_data, data_object_id)
