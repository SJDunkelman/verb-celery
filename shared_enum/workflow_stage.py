from enum import Enum


class WorkflowStage(str, Enum):
    VIEWING = "VIEWING"
    EDITING = "EDITING"
    QA = "QA"
    LIVE = "LIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    CONVERSING = "CONVERSING"
