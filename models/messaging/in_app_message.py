from pydantic import BaseModel, UUID4
from shared_enum.message_role import MessageRole
from datetime import datetime


class InAppMessageBase(BaseModel):
    role: MessageRole
    message: str
    user_id: UUID4 | None = None


class InAppMessageCreate(InAppMessageBase):
    workflow_id: UUID4


class InAppMessage(InAppMessageBase):
    created_at: datetime
