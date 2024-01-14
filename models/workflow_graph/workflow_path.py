from pydantic import BaseModel, UUID4
from models.workflow_graph.node import Node
from models.workflow_graph.edge import Edge


class Pathway(BaseModel):
    nodes: list[Node] = []
    edges: dict[UUID4, list[Edge]] = {}

    def add_node(self, node: Node):
        # Add a node to the pathway
        self.nodes.append(node)

    def add_edge(self, edge: Edge):
        # Add an edge between nodes in the pathway
        if edge.from_node_id not in self.edges:
            self.edges[edge.from_node_id] = []
        self.edges[edge.from_node_id].append(edge)

    def get_adjacent_nodes(self, node_id: UUID4) -> list[UUID4]:
        # Get a list of nodes that are adjacent to the given node
        return [edge.to_node_id for edge in self.edges.get(node_id, [])]

    def get_next_node(self, current_node_id: UUID4) -> UUID4:
        # Get the next node after the current node based on the edges
        # In a more complex scenario, this may involve decision logic
        adjacent_nodes = self.get_adjacent_nodes(current_node_id)
        return adjacent_nodes[0] if adjacent_nodes else None
