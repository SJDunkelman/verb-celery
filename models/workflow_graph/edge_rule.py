from pydantic import BaseModel, UUID4


class EdgeRule(BaseModel):
    id: UUID4
    class_name: str
    description: str | None = None
    rule_order: int
