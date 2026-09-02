from typing import List, Optional
from pydantic import BaseModel


class TestStep(BaseModel):
    step_number: int
    action: str
    expected: str


class TestCaseModel(BaseModel):
    test_case_id: str
    requirement_id: str
    scenario_id: str
    title: str
    test_type: Optional[str] = None
    priority: Optional[str] = "Medium"
    preconditions: Optional[List[str]] = []
    test_data: Optional[dict] = {}
    test_steps: List[TestStep] = []
    expected_result: str
    postconditions: Optional[List[str]] = []
    positive: Optional[bool] = True
    boundary_category: Optional[str] = None
    automation_candidate: Optional[bool] = False
    source_reference: Optional[str] = None


class TestCasePackage(BaseModel):
    test_cases: List[TestCaseModel] = []
    total: int = 0
