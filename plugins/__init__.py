from .external_service_automation.linkedin_lead_list.process_node import GenerateLeadListLinkedInNode


# Registry of available plugin classes
available_plugins = {
    'GenerateLeadListLinkedInNode': GenerateLeadListLinkedInNode,
    # Add other plugin classes here
}