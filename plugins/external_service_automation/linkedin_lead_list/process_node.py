from workflow.data_object import DataObject
from workflow.node import ProcessNode
from typing import Any
from context.knowledge.target_customer import TargetCustomer
from ai import fsystem, fuser, gpt4_ai
from utils.llm_parsing import parse_dict_from_llm_bullet_points
from plugins.external_service_automation.linkedin_lead_list.linkedin_filters import LinkedInLeadFilter
from plugins.external_service_automation.linkedin_lead_list.lix_vendor_functions import (
    create_linkedin_search_url,
    get_linkedin_search_facets,
    get_linkedin_sales_navigator_leads)


class GenerateLeadListLinkedInNode(ProcessNode):
    def execute(self, data_object: DataObject) -> Any:
        target_customer = self.get_context_item("TargetCustomer", data_object)
        linkedin_filters = self.convert_target_customer_to_linkedin_lead_filters(target_customer)
        filter_values = self.refine_linkedin_filter_values(linkedin_filters)

        # Get search facets and save to DB
        search_facets = get_linkedin_search_facets(filter_values)
        # Get leads from LinkedIn
        search_url = create_linkedin_search_url(filter_values)
        leads = get_linkedin_sales_navigator_leads(search_url, 100)
        # Save leads to database

        # Get emails for leads
        # return lead list

    @classmethod
    def convert_target_customer_to_linkedin_lead_filters(cls,
                                                         target_customer: TargetCustomer
                                                         ) -> list[tuple[LinkedInLeadFilter, str]]:
        filters = []
        if target_customer.employer:
            filters.append((LinkedInLeadFilter.COMPANY, target_customer.employer))
        if target_customer.industry:
            filters.append((LinkedInLeadFilter.INDUSTRY, target_customer.industry))
        if target_customer.job_title:
            filters.append((LinkedInLeadFilter.TITLE, target_customer.job_title))
        if target_customer.job_seniority:
            filters.append((LinkedInLeadFilter.SENIORITY, target_customer.job_seniority))
        if target_customer.job_function:
            filters.append((LinkedInLeadFilter.FUNCTION, target_customer.job_function))
        if target_customer.location:
            filters.append((LinkedInLeadFilter.BING_GEO, target_customer.location))
        return filters

    def refine_linkedin_filter_values(self,
                                      linkedin_filters: list[tuple[LinkedInLeadFilter, str]]
                                      ) -> dict[LinkedInLeadFilter, str | list[str]]:
        system_prompt = open(self.directory / "prompts" / "linkedin_filter_converter").read()
        user_message = "\n".join(
            [f"{linkedin_filter[0].value.upper()}: {linkedin_filter[1]}" for linkedin_filter in linkedin_filters])
        response = gpt4_ai.chat_completion(
            messages=[fsystem(system_prompt), fuser(user_message)],
            temperature=0.4
        )
        filters = parse_dict_from_llm_bullet_points(response)
        return {LinkedInLeadFilter(key.upper()): value for key, value in filters.items()}


if __name__ == "__main__":
    from core.workflow.data_object import DataObject
    from core.context.knowledge.target_customer import TargetCustomer
    from core.workflow.pathway import WorkflowPathway
    from core.utils.pydantic_utils import create_model_instances_from_context_json
    import json
    from core.db import supabase_client
    from core import context as context_models

    target_customer = TargetCustomer(
        employer="Google",
        job_title="Software Engineer",
        job_seniority="Senior"
    )

    data_obj_data = '{"created_by_user_id": "ed7d05b9-63e2-429a-88fd-f23aa83c8572", "created_at": "2024-01-11T00:09:27.487816", "last_modified_by_user_id": "ed7d05b9-63e2-429a-88fd-f23aa83c8572", "last_modified_at": "2024-01-11T00:09:27.487826", "current_status": "COMPLETED", "current_workflow_node_id": "62817448-458c-4c3d-a2e8-5f8ce6606b7f", "previous_node_status": null, "previous_workflow_node_id": null, "intent": "COMPLETE", "pathway_id": "bde58f5c-8004-40db-9cf3-4d80d18d58f1", "target_node_id": null, "context": {}, "data_object_id": "6c129812-55af-45fd-9394-7aa6e08d9877", "workflow_id": "df629f3c-ffc2-43e8-8375-bfda84415aa3"}'
    data_obj_dict = json.loads(data_obj_data)
    data_obj = DataObject.create_from_dict(data_obj_dict)

    workflow_id = data_obj_dict['workflow_id']

    workflow_pathway = WorkflowPathway(workflow_id=workflow_id, pathway_id=data_obj_dict['pathway_id'])
    workflow_pathway.load_pathway_nodes()
    next_workflow_node = workflow_pathway.get_next_node(data_obj.metadata.current_workflow_node_id)
    next_workflow_node_id = next_workflow_node['workflow_node_id']
    data_obj.move_to_next_node(next_workflow_node_id)

    data_obj.add_context_item_pydantic(target_customer)

    node_context_result = supabase_client.table('workflow_node_context').select('context').eq('node_id',
                                                                                              next_workflow_node_id).order(
        'timestamp', desc=True).limit(1).execute()
    if node_context_result.data:
        node_context_dict = node_context_result.data[0]['context']
        node_context = create_model_instances_from_context_json(context_models, node_context_dict)
    else:
        node_context = {}
    test_node = GenerateLeadListLinkedInNode(workflow_node_id=next_workflow_node_id, context=node_context)
    test_node.load_context()
    test_node.execute(data_obj)
