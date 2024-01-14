from pydantic import BaseModel
from datetime import datetime
from shared_enum.message_role import MessageRole
from context.base_knowledge import BaseKnowledge


class AgentConversation(BaseModel):
    id: int
    workflow_node_id: str
    object_class_name: str


class AgentConversationMessage(BaseModel):
    created_at: datetime
    role: MessageRole
    message: str
    extracted_model: BaseKnowledge | None = None
