from workflow.node import Node
from typing import Any


class Edge:
    def __init__(self, from_node: Node, to_node: Node, rules: list = None):
        self.from_node = from_node
        self.to_node = to_node
        self.rules = rules or []

    def can_transition(self, data: Any) -> bool:
        if self.rules:
            return all(rule.evaluate(data) for rule in self.rules)
        return True
