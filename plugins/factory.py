from plugins import available_plugins


def get_node_class(node_class_name: str):
    # Fetch the class from the registry
    node_class = available_plugins.get(node_class_name)
    if not node_class:
        raise ValueError(f"No plugin class found for {node_class_name}")
    return node_class
