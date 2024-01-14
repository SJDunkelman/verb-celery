from pydantic import Field
from context.base_knowledge import BaseKnowledge


class TargetCustomer(BaseKnowledge):
    employer: str | None = Field(description="The target customer's current employer", default=None)
    company_size: str | None = Field(description="The size of the target customer's current employer", default=None)
    industry: str | None = Field(description="The industry the target customer works in", default=None)
    job_title: str | None = Field(description="The target customer's current job title", default=None)
    location: str | None = Field(description="The location where the target customer is based", default=None)
    job_seniority: str | None = Field(description="The seniority of the target customer at their current employer", default=None)
    job_function: str | None = Field(description="The function of the company the target customer works in", default=None)

    @classmethod
    def initial_message(cls) -> str:
        return "Please describe your target customer"

    @classmethod
    def confirmation_message(cls) -> str:
        return "Here's the target customer I've extracted, is this correct?"
