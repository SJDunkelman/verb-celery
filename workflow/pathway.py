from db import supabase_client


class WorkflowPathway:
    def __init__(self, workflow_id: str, pathway_id: str):
        self.workflow_id = workflow_id
        self.pathway_id = pathway_id
        self.pathway_nodes = []

    def load_pathway_nodes(self):
        workflow_nodes_result = supabase_client.rpc('get_workflow_pathway_nodes', params={'input_workflow_id': self.workflow_id,
                                                                                   'input_pathway_id': self.pathway_id}).execute()
        self.pathway_nodes = workflow_nodes_result.data

    def get_input_node_id(self, class_name: str | None = None) -> str:
        """
        Returns a specific input node id if class_name is specified, otherwise returns first input node
        :param class_name:
        :return:
        """
        input_nodes = [node for node in self.pathway_nodes if node['base_type'] == 'input']
        if class_name:
            input_nodes = [node for node in input_nodes if node['class_name'] == class_name]
        return input_nodes[0]['workflow_node_id']

    def get_next_node(self, current_node_id: str) -> dict | None:
        sorted_nodes = sorted(self.pathway_nodes, key=lambda x: x['sequence_order'])

        for i, node in enumerate(sorted_nodes):
            if str(node['workflow_node_id']) == str(current_node_id):
                if i + 1 < len(sorted_nodes):
                    return sorted_nodes[i + 1]
                else:
                    return None  # No next node
