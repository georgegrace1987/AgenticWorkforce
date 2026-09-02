from pydantic import BaseModel, Field


class RequirementState(BaseModel):
    business_objective: str | None = None
    stakeholders: list[str] = Field(default_factory=list)
    user_roles: list[str] = Field(default_factory=list)
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    asked_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    answered_topics: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=10000)
    
class GenerateRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    requirements: RequirementState
    readiness_score: int
    readiness_items: dict[str, bool]
    open_questions: list[str]
