"""Deterministic validation of generated test artifacts.

This module provides validation functions that check structural integrity,
traceability, and data quality without relying on LLM reasoning.
"""

from typing import List, Dict, Set, Tuple, Any, Optional
from pydantic import BaseModel

from src.models.requirement_models import RequirementPackage
from src.models.scenario_models import ScenarioPackage
from src.models.testcase_models import TestCasePackage
from src.utils.logger import get_logger

logger = get_logger("deterministic_validator")


class ValidationIssue(BaseModel):
    """A single validation issue found during validation."""

    severity: str  # "error", "warning", "info"
    category: str  # "structural", "traceability", "duplicate", "quality"
    message: str
    affected_items: List[str] = []  # IDs of affected items


class ValidationResult(BaseModel):
    """Result of a validation run."""

    is_valid: bool
    total_issues: int = 0
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []
    info: List[ValidationIssue] = []
    summary: Dict[str, Any] = {}

    @property
    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation found any warnings."""
        return len(self.warnings) > 0

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add an issue to the validation result."""
        if issue.severity == "error":
            self.errors.append(issue)
        elif issue.severity == "warning":
            self.warnings.append(issue)
        else:
            self.info.append(issue)
        self.total_issues += 1


class DeterministicValidator:
    """Validates test artifacts using deterministic rules.

    Checks:
    - Structural integrity (required fields, valid formats)
    - Referential integrity (IDs exist, no orphans)
    - Uniqueness (no duplicate IDs)
    - Traceability (proper relationships)
    - Basic quality metrics
    """

    def __init__(self):
        pass

    def validate_requirements(self, requirements: RequirementPackage) -> ValidationResult:
        """Validate a requirement package.

        Args:
            requirements: The RequirementPackage to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(is_valid=True)

        if not requirements or not requirements.requirements:
            issue = ValidationIssue(
                severity="error",
                category="structural",
                message="No requirements in package",
            )
            result.add_issue(issue)
            result.is_valid = False
            return result

        requirement_ids: Set[str] = set()
        for idx, req in enumerate(requirements.requirements):
            # Check required fields
            if not req.requirement_id:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Requirement {idx + 1}: missing requirement_id",
                    affected_items=[str(idx)],
                )
                result.add_issue(issue)
                result.is_valid = False

            if not req.requirement_text:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Requirement {req.requirement_id}: missing requirement_text",
                    affected_items=[req.requirement_id],
                )
                result.add_issue(issue)
                result.is_valid = False

            # Check uniqueness
            if req.requirement_id in requirement_ids:
                issue = ValidationIssue(
                    severity="error",
                    category="duplicate",
                    message=f"Duplicate requirement_id: {req.requirement_id}",
                    affected_items=[req.requirement_id],
                )
                result.add_issue(issue)
                result.is_valid = False
            else:
                requirement_ids.add(req.requirement_id)

            # Quality checks
            if req.requirement_text and len(req.requirement_text) > 500:
                issue = ValidationIssue(
                    severity="warning",
                    category="quality",
                    message=f"Requirement {req.requirement_id}: text is very long ({len(req.requirement_text)} chars)",
                    affected_items=[req.requirement_id],
                )
                result.add_issue(issue)

        result.summary = {
            "total_requirements": len(requirements.requirements),
            "unique_ids": len(requirement_ids),
            "error_count": len(result.errors),
        }
        return result

    def validate_scenarios(
        self, scenarios: ScenarioPackage, requirements: Optional[RequirementPackage] = None
    ) -> ValidationResult:
        """Validate a scenario package.

        Args:
            scenarios: The ScenarioPackage to validate
            requirements: Optional RequirementPackage for traceability checks

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(is_valid=True)

        if not scenarios or not scenarios.scenarios:
            issue = ValidationIssue(
                severity="warning",
                category="structural",
                message="No scenarios in package",
            )
            result.add_issue(issue)
            return result

        scenario_ids: Set[str] = set()
        requirement_ids: Set[str] = set()

        if requirements:
            requirement_ids = {req.requirement_id for req in requirements.requirements}

        for idx, scenario in enumerate(scenarios.scenarios):
            # Check required fields
            if not scenario.scenario_id:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Scenario {idx + 1}: missing scenario_id",
                    affected_items=[str(idx)],
                )
                result.add_issue(issue)
                result.is_valid = False

            if not scenario.requirement_id:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Scenario {scenario.scenario_id}: missing requirement_id",
                    affected_items=[scenario.scenario_id],
                )
                result.add_issue(issue)
                result.is_valid = False

            if not scenario.scenario_title:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Scenario {scenario.scenario_id}: missing scenario_title",
                    affected_items=[scenario.scenario_id],
                )
                result.add_issue(issue)
                result.is_valid = False

            # Check uniqueness
            if scenario.scenario_id in scenario_ids:
                issue = ValidationIssue(
                    severity="error",
                    category="duplicate",
                    message=f"Duplicate scenario_id: {scenario.scenario_id}",
                    affected_items=[scenario.scenario_id],
                )
                result.add_issue(issue)
                result.is_valid = False
            else:
                scenario_ids.add(scenario.scenario_id)

            # Check traceability
            if requirements and scenario.requirement_id not in requirement_ids:
                issue = ValidationIssue(
                    severity="error",
                    category="traceability",
                    message=f"Scenario {scenario.scenario_id}: references non-existent requirement {scenario.requirement_id}",
                    affected_items=[scenario.scenario_id],
                )
                result.add_issue(issue)
                result.is_valid = False

        result.summary = {
            "total_scenarios": len(scenarios.scenarios),
            "unique_ids": len(scenario_ids),
            "error_count": len(result.errors),
        }
        return result

    def validate_test_cases(
        self, test_cases: TestCasePackage, scenarios: Optional[ScenarioPackage] = None,
        requirements: Optional[RequirementPackage] = None,
    ) -> ValidationResult:
        """Validate a test case package.

        Args:
            test_cases: The TestCasePackage to validate
            scenarios: Optional ScenarioPackage for traceability checks
            requirements: Optional RequirementPackage for traceability checks

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(is_valid=True)

        if not test_cases or not test_cases.test_cases:
            issue = ValidationIssue(
                severity="warning",
                category="structural",
                message="No test cases in package",
            )
            result.add_issue(issue)
            return result

        test_case_ids: Set[str] = set()
        scenario_ids: Set[str] = set()
        requirement_ids: Set[str] = set()

        if scenarios:
            scenario_ids = {s.scenario_id for s in scenarios.scenarios}
        if requirements:
            requirement_ids = {r.requirement_id for r in requirements.requirements}

        for idx, tc in enumerate(test_cases.test_cases):
            # Check required fields
            if not tc.test_case_id:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Test Case {idx + 1}: missing test_case_id",
                    affected_items=[str(idx)],
                )
                result.add_issue(issue)
                result.is_valid = False

            if not tc.title:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Test Case {tc.test_case_id}: missing title",
                    affected_items=[tc.test_case_id],
                )
                result.add_issue(issue)
                result.is_valid = False

            if not tc.expected_result:
                issue = ValidationIssue(
                    severity="error",
                    category="structural",
                    message=f"Test Case {tc.test_case_id}: missing expected_result",
                    affected_items=[tc.test_case_id],
                )
                result.add_issue(issue)
                result.is_valid = False

            # Check test steps
            if not tc.test_steps:
                issue = ValidationIssue(
                    severity="warning",
                    category="quality",
                    message=f"Test Case {tc.test_case_id}: has no test steps defined",
                    affected_items=[tc.test_case_id],
                )
                result.add_issue(issue)
            else:
                for step_idx, step in enumerate(tc.test_steps):
                    if not step.action:
                        issue = ValidationIssue(
                            severity="error",
                            category="structural",
                            message=f"Test Case {tc.test_case_id}, Step {step_idx + 1}: missing action",
                            affected_items=[tc.test_case_id],
                        )
                        result.add_issue(issue)
                        result.is_valid = False

                    if not step.expected:
                        issue = ValidationIssue(
                            severity="error",
                            category="structural",
                            message=f"Test Case {tc.test_case_id}, Step {step_idx + 1}: missing expected result",
                            affected_items=[tc.test_case_id],
                        )
                        result.add_issue(issue)
                        result.is_valid = False

            # Check uniqueness
            if tc.test_case_id in test_case_ids:
                issue = ValidationIssue(
                    severity="error",
                    category="duplicate",
                    message=f"Duplicate test_case_id: {tc.test_case_id}",
                    affected_items=[tc.test_case_id],
                )
                result.add_issue(issue)
                result.is_valid = False
            else:
                test_case_ids.add(tc.test_case_id)

            # Check traceability
            if requirements and tc.requirement_id not in requirement_ids:
                issue = ValidationIssue(
                    severity="error",
                    category="traceability",
                    message=f"Test Case {tc.test_case_id}: references non-existent requirement {tc.requirement_id}",
                    affected_items=[tc.test_case_id],
                )
                result.add_issue(issue)
                result.is_valid = False

            if scenarios and tc.scenario_id not in scenario_ids:
                issue = ValidationIssue(
                    severity="error",
                    category="traceability",
                    message=f"Test Case {tc.test_case_id}: references non-existent scenario {tc.scenario_id}",
                    affected_items=[tc.test_case_id],
                )
                result.add_issue(issue)
                result.is_valid = False

        result.summary = {
            "total_test_cases": len(test_cases.test_cases),
            "unique_ids": len(test_case_ids),
            "automation_candidates": sum(1 for tc in test_cases.test_cases if tc.automation_candidate),
            "error_count": len(result.errors),
        }
        return result

    def validate_traceability(
        self, requirements: RequirementPackage, scenarios: ScenarioPackage, test_cases: TestCasePackage
    ) -> ValidationResult:
        """Validate end-to-end traceability.

        Checks that requirements have scenarios and test cases covering them.

        Args:
            requirements: RequirementPackage
            scenarios: ScenarioPackage
            test_cases: TestCasePackage

        Returns:
            ValidationResult with traceability issues
        """
        result = ValidationResult(is_valid=True)

        requirement_ids = {r.requirement_id for r in requirements.requirements}
        scenario_ids = {s.scenario_id for s in scenarios.scenarios}
        test_case_ids = {tc.test_case_id for tc in test_cases.test_cases}

        # Map requirements to scenarios
        req_to_scenarios: Dict[str, Set[str]] = {rid: set() for rid in requirement_ids}
        for scenario in scenarios.scenarios:
            if scenario.requirement_id in req_to_scenarios:
                req_to_scenarios[scenario.requirement_id].add(scenario.scenario_id)

        # Map scenarios to test cases
        scenario_to_tests: Dict[str, Set[str]] = {sid: set() for sid in scenario_ids}
        for tc in test_cases.test_cases:
            if tc.scenario_id in scenario_to_tests:
                scenario_to_tests[tc.scenario_id].add(tc.test_case_id)

        # Check for requirements with no scenarios
        uncovered_requirements = []
        for req_id in requirement_ids:
            if not req_to_scenarios[req_id]:
                issue = ValidationIssue(
                    severity="warning",
                    category="traceability",
                    message=f"Requirement {req_id}: has no test scenarios",
                    affected_items=[req_id],
                )
                result.add_issue(issue)
                uncovered_requirements.append(req_id)

        # Check for scenarios with no test cases
        uncovered_scenarios = []
        for scenario_id in scenario_ids:
            if not scenario_to_tests[scenario_id]:
                issue = ValidationIssue(
                    severity="warning",
                    category="traceability",
                    message=f"Scenario {scenario_id}: has no test cases",
                    affected_items=[scenario_id],
                )
                result.add_issue(issue)
                uncovered_scenarios.append(scenario_id)

        result.summary = {
            "total_requirements": len(requirement_ids),
            "covered_requirements": len(requirement_ids) - len(uncovered_requirements),
            "coverage_percentage": (
                (len(requirement_ids) - len(uncovered_requirements)) / len(requirement_ids) * 100
                if requirement_ids else 0
            ),
            "uncovered_requirements": uncovered_requirements,
            "uncovered_scenarios": uncovered_scenarios,
        }
        return result
