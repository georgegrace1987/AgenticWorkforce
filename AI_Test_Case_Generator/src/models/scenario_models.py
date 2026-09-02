from typing import List, Optional
from pydantic import BaseModel


class ScenarioModel(BaseModel):
    scenario_id: str
    requirement_id: str
    scenario_title: str
    scenario_description: Optional[str] = None
    scenario_type: Optional[str] = None
    priority: Optional[str] = "Medium"
    rationale: Optional[str] = None
    source_reference: Optional[str] = None


class ScenarioPackage(BaseModel):
    scenarios: List[ScenarioModel] = []
    total: int = 0
