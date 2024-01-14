from pydantic import BaseModel, UUID4, Field, ConfigDict
from datetime import datetime
from shared_enum.data_object_status import DataObjectStatus


class Metadata(BaseModel):
    created_by_user_id: UUID4
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified_by_user_id: UUID4
    last_modified_at: datetime = Field(default_factory=datetime.utcnow)
    current_status: DataObjectStatus
    current_workflow_node_id: UUID4
    previous_node_status: DataObjectStatus | None = None
    previous_workflow_node_id: UUID4 | None = None

    model_config = ConfigDict(validate_assignment=True)

    def update(self, **new_data):
        for field, value in new_data.items():
            setattr(self, field, value)
