

class ContextMissingError(Exception):
    """Raised when a needed item is missing from the context of a node and/or data object"""

    def __init__(self, message, missing_context_class_names: list[str]):
        super().__init__(message)
        self.missing_context_class_names = missing_context_class_names

    def __reduce__(self):
        return self.__class__, (self.missing_context_class_names,)


class NodeExecutionError(Exception):
    """Raised when a node fails to execute"""
    pass


class DataContentError(Exception):
    """Raised when a data content is missing or corrupted when used by a node (typically further down pathway)"""
    pass
