from typing import List, Optional
from pydantic import BaseModel, Field


class RequirementModel(BaseModel):
    requirement_id: str = Field(..., description="Unique requirement identifier")
    requirement_text: str
    requirement_type: str
    priority: Optional[str] = "Medium"
    source_file: Optional[str]
    source_location: Optional[str]
    dependencies: Optional[List[str]] = []
    business_rules: Optional[List[str]] = []
    ambiguities: Optional[List[str]] = []
    assumptions: Optional[List[str]] = []


class RequirementPackage(BaseModel):
    requirements: List[RequirementModel] = []
    total: int = 0
