from typing import Any


class NodeSetting:
    def __init__(self, value: Any, data_object: Any, nodes: list[Any]):
        self.value = value
        self.data_object = data_object
        self.nodes = nodes
        self.check_constraints()

    def check_constraints(self):
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError
