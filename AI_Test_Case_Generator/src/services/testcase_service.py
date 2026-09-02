import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from src.agents.requirement_agent import RequirementAgent
from src.document_processing.document_loader import load_documents
from src.document_processing.document_normalizer import normalize_documents
from src.exporters.excel_exporter import export_test_assets
from src.models.document_models import DocumentModel
from src.models.requirement_models import RequirementPackage, RequirementModel
from src.models.scenario_models import ScenarioModel, ScenarioPackage
from src.models.testcase_models import TestCaseModel, TestCasePackage, TestStep
from src.orchestration.orchestrator import AgentOrchestrator
from src.orchestration.workflow_state import WorkflowState
from src.prompts.testcase_prompts import build_testcase_generation_prompt
from src.validation.deterministic_validator import DeterministicValidator
from src.utils.logger import get_logger

logger = get_logger("testcase_service")


class TestCaseService:
    def __init__(self, provider: str | None = None, state_dir: Path | None = None):
        self.requirement_agent = RequirementAgent(provider=provider)
        self.orchestrator = AgentOrchestrator(state_dir=state_dir)
        self.orchestrator.register_agent(self.requirement_agent)
        self.validator = DeterministicValidator()

    def _summarize_requirements(self, requirements: RequirementPackage) -> str:
        lines = []
        for req in requirements.requirements:
            lines.append(
                f"{req.requirement_id}: {req.requirement_text} "
                f"(type={req.requirement_type}, priority={req.priority}, source={req.source_file or 'Not specified'})"
            )
        return "\n".join(lines)

    def _fallback_generate(self, requirements: RequirementPackage) -> tuple[list[str], ScenarioPackage, TestCasePackage]:
        outline = [f"{req.requirement_id}: {req.requirement_text}" for req in requirements.requirements]
        scenarios: list[ScenarioModel] = []
        test_cases: list[TestCaseModel] = []
        for idx, req in enumerate(requirements.requirements, start=1):
            scenario_id = f"SCN-{idx:03d}"
            tc_id = f"TC-{idx:03d}"
            scenarios.append(
                ScenarioModel(
                    scenario_id=scenario_id,
                    requirement_id=req.requirement_id,
                    scenario_title=f"Validate {req.requirement_text[:60]}",
                    scenario_description=req.requirement_text,
                    scenario_type=req.requirement_type,
                    priority=req.priority,
                    rationale="Derived from source requirement",
                    source_reference=req.source_file,
                )
            )
            test_cases.append(
                TestCaseModel(
                    test_case_id=tc_id,
                    requirement_id=req.requirement_id,
                    scenario_id=scenario_id,
                    title=f"Verify {req.requirement_text[:50]}",
                    test_type=req.requirement_type,
                    priority=req.priority,
                    preconditions=["Relevant application screen is available"],
                    test_data={},
                    test_steps=[
                        TestStep(step_number=1, action="Open the related application flow", expected="User reaches the correct screen"),
                        TestStep(step_number=2, action="Perform the required action", expected="System processes the request"),
                    ],
                    expected_result=req.requirement_text,
                    postconditions=["System state remains valid"],
                    positive=True,
                    boundary_category="Functional",
                    automation_candidate=True,
                    source_reference=req.source_file,
                )
            )
        return outline, ScenarioPackage(scenarios=scenarios, total=len(scenarios)), TestCasePackage(test_cases=test_cases, total=len(test_cases))

    def generate_artifacts(self, docs: List[DocumentModel], export_dir: Path) -> Dict[str, Any]:
        """Generate test artifacts using the orchestration framework.

        Args:
            docs: List of normalized documents
            export_dir: Directory to export results to

        Returns:
            Dictionary with results and any errors
        """
        try:
            # Create workflow state
            workflow_id = str(uuid.uuid4())
            state = WorkflowState(
                workflow_id=workflow_id,
                documents=docs,
                raw_input=f"Document batch with {len(docs)} files",
            )

            # Execute orchestrator
            logger.info(f"Starting workflow: {workflow_id}")
            state = self.orchestrator.execute(state, fail_on_error=False)

            # Check if we got requirements
            if not state.requirements or not state.requirements.requirements:
                return {"error": "No requirements could be extracted from the uploaded documents."}

            # Validate requirements
            validation_result = self.validator.validate_requirements(state.requirements)
            state.validation_results.append(validation_result.model_dump())

            # Generate scenarios and test cases (fallback for now)
            summary = self._summarize_requirements(state.requirements)
            prompt = build_testcase_generation_prompt(summary)
            outline, scenarios_pkg, cases_pkg = self._fallback_generate(state.requirements)

            # Store in state
            state.scenarios = scenarios_pkg
            state.test_cases = cases_pkg

            # Validate scenarios
            scenario_validation = self.validator.validate_scenarios(scenarios_pkg, state.requirements)
            state.validation_results.append(scenario_validation.model_dump())

            # Validate test cases
            tc_validation = self.validator.validate_test_cases(cases_pkg, scenarios_pkg, state.requirements)
            state.validation_results.append(tc_validation.model_dump())

            # Validate traceability
            traceability_validation = self.validator.validate_traceability(state.requirements, scenarios_pkg, cases_pkg)
            state.validation_results.append(traceability_validation.model_dump())

            # Try to enhance with LLM if available
            client = self.requirement_agent.client
            if client.health_check():
                try:
                    resp = client.generate_structured(prompt, schema={})
                    payload = {}
                    if isinstance(resp, dict):
                        if "choices" in resp and resp["choices"]:
                            content = resp["choices"][0].get("message", {}).get("content") or resp["choices"][0].get("text")
                            payload = json.loads(content) if content else {}
                        else:
                            payload = resp
                    outline = payload.get("requirements_outline", outline) or outline
                    scenarios = payload.get("scenarios", [])
                    test_cases = payload.get("test_cases", [])
                    if scenarios:
                        scenarios_pkg = ScenarioPackage(scenarios=[ScenarioModel(**item) for item in scenarios], total=len(scenarios))
                        state.scenarios = scenarios_pkg
                    if test_cases:
                        parsed_cases = []
                        for item in test_cases:
                            steps = [TestStep(**step) for step in item.get("test_steps", [])]
                            item = {**item, "test_steps": steps}
                            parsed_cases.append(TestCaseModel(**item))
                        cases_pkg = TestCasePackage(test_cases=parsed_cases, total=len(parsed_cases))
                        state.test_cases = cases_pkg
                except Exception:
                    logger.exception("LLM generation failed; using fallback scenarios/test cases")

            # Export results
            export_path = export_test_assets(export_dir, state.requirements, state.scenarios or scenarios_pkg, state.test_cases or cases_pkg)
            state.export_path = str(export_path)

            # Store workflow state
            self.orchestrator.save_state(state)

            return {
                "requirements": state.requirements,
                "outline": outline,
                "scenarios": state.scenarios or scenarios_pkg,
                "test_cases": state.test_cases or cases_pkg,
                "export_path": export_path,
                "workflow_id": workflow_id,
                "validation_results": state.validation_results,
            }

        except Exception as e:
            logger.exception(f"Error generating artifacts: {e}")
            return {"error": str(e)}
