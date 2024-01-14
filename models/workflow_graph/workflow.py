from pydantic import BaseModel, UUID4


class WorkflowBase(BaseModel):
    id: UUID4
