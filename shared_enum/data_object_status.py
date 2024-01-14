from enum import Enum


class DataObjectStatus(Enum):
    ERROR = 'ERROR'
    PENDING = 'PENDING'  # When waiting for an external service like a vendor API
    WAITING = 'WAITING'  # When waiting for an input such as a message from a user (internal or external)
    IN_PROGRESS = 'IN_PROGRESS'  # When processing at a node
    CANCELLED = 'CANCELLED'
    CONVERSING = 'CONVERSING'  # When in an agent conversation such as to extract a context item or resolve an error
    COMPLETED = 'COMPLETED'  # When the data object has reached the end of its path / target node and been processed

    def __str__(self):
        return self.value
