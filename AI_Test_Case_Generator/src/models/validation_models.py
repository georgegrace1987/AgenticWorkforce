from typing import List, Optional
from pydantic import BaseModel


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "warning"
    related_ids: Optional[List[str]] = []


class ValidationReport(BaseModel):
    total_requirements: int = 0
    covered_requirements: int = 0
    uncovered_requirements: int = 0
    total_scenarios: int = 0
    total_test_cases: int = 0
    duplicate_test_cases: int = 0
    coverage_percentage: float = 0.0
    issues: List[ValidationIssue] = []
    recommendations: Optional[List[str]] = []
