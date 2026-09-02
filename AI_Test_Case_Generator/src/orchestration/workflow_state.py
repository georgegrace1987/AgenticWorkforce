"""Central workflow state management for the AI Test Case Generator.

This module defines the WorkflowState class which tracks all data
flowing through the agent orchestration pipeline, including execution
history, status, and errors.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.models.document_models import DocumentModel
from src.models.requirement_models import RequirementPackage
from src.models.scenario_models import ScenarioPackage
from src.models.testcase_models import TestCasePackage
from src.utils.logger import get_logger

logger = get_logger("workflow_state")


class WorkflowStatus(str, Enum):
    """Workflow execution status enumeration."""

    RECEIVED = "received"
    PARSED = "parsed"
    ANALYZED = "analyzed"
    SCENARIOS_GENERATED = "scenarios_generated"
    TEST_CASES_GENERATED = "test_cases_generated"
    VALIDATED = "validated"
    COVERAGE_ANALYZED = "coverage_analyzed"
    UI_CLASSIFIED = "ui_classified"
    AUTOMATION_GENERATED = "automation_generated"
    EXPORTED = "exported"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentExecutionRecord(BaseModel):
    """Record of a single agent execution."""

    agent_name: str
    status: str  # "pending", "running", "success", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_started(self) -> None:
        """Mark agent as started."""
        self.status = "running"
        self.start_time = datetime.now()

    def mark_completed(self) -> None:
        """Mark agent as successfully completed."""
        self.status = "success"
        self.end_time = datetime.now()
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_ms = int(delta.total_seconds() * 1000)

    def mark_failed(self, error: str) -> None:
        """Mark agent as failed with error message."""
        self.status = "failed"
        self.error_message = error
        self.end_time = datetime.now()
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_ms = int(delta.total_seconds() * 1000)


class WorkflowState(BaseModel):
    """Central state object for the entire workflow execution.

    Tracks all data flowing through the pipeline, maintains execution
    history, and provides checkpoints for error recovery.
    """

    # Identification
    workflow_id: str = Field(..., description="Unique workflow identifier")
    request_timestamp: datetime = Field(default_factory=datetime.now)

    # Status tracking
    status: WorkflowStatus = Field(default=WorkflowStatus.RECEIVED)
    completed_at: Optional[datetime] = None

    # Input data
    raw_input: str = Field(default="", description="Original input text or file path")
    documents: List[DocumentModel] = Field(default_factory=list)

    # Processed data at each stage
    requirements: Optional[RequirementPackage] = None
    scenarios: Optional[ScenarioPackage] = None
    test_cases: Optional[TestCasePackage] = None

    # Analysis results
    coverage_analysis: Dict[str, Any] = Field(default_factory=dict)
    ui_classifications: Dict[str, Any] = Field(default_factory=dict)
    automation_artifacts: Dict[str, Any] = Field(default_factory=dict)

    # Quality tracking
    validation_results: List[Dict[str, Any]] = Field(default_factory=list)
    uncovered_requirements: List[str] = Field(default_factory=list)

    # Execution tracking
    agent_history: List[AgentExecutionRecord] = Field(default_factory=list)

    # Error and warning collection
    errors: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)
    clarifications_needed: List[Dict[str, Any]] = Field(default_factory=list)

    # Export data
    export_path: Optional[str] = None

    def add_error(self, agent: str, error_message: str, severity: str = "error") -> None:
        """Add an error to the workflow error log."""
        self.errors.append({
            "agent": agent,
            "message": error_message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        })
        logger.error(f"[{agent}] {error_message}")

    def add_warning(self, agent: str, warning_message: str) -> None:
        """Add a warning to the workflow warning log."""
        self.warnings.append({
            "agent": agent,
            "message": warning_message,
            "timestamp": datetime.now().isoformat(),
        })
        logger.warning(f"[{agent}] {warning_message}")

    def add_clarification(self, question: str, context: str = "", priority: str = "medium") -> None:
        """Add a clarification question that requires human input."""
        self.clarifications_needed.append({
            "question": question,
            "context": context,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        })
        logger.info(f"[CLARIFICATION] {question}")

    def get_agent_record(self, agent_name: str) -> Optional[AgentExecutionRecord]:
        """Get execution record for a specific agent."""
        for record in self.agent_history:
            if record.agent_name == agent_name:
                return record
        return None

    def create_agent_record(self, agent_name: str) -> AgentExecutionRecord:
        """Create and register a new agent execution record."""
        record = AgentExecutionRecord(
            agent_name=agent_name,
            status="pending",
        )
        self.agent_history.append(record)
        logger.info(f"Created execution record for agent: {agent_name}")
        return record

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution."""
        successful_agents = sum(1 for r in self.agent_history if r.status == "success")
        failed_agents = sum(1 for r in self.agent_history if r.status == "failed")
        total_duration_ms = sum(r.duration_ms or 0 for r in self.agent_history if r.duration_ms)

        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "total_agents_executed": len(self.agent_history),
            "successful": successful_agents,
            "failed": failed_agents,
            "total_duration_ms": total_duration_ms,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "clarification_count": len(self.clarifications_needed),
            "requirements_count": len(self.requirements.requirements) if self.requirements else 0,
            "scenarios_count": len(self.scenarios.scenarios) if self.scenarios else 0,
            "test_cases_count": len(self.test_cases.test_cases) if self.test_cases else 0,
            "completed_at": self.completed_at,
        }

    def transition_status(self, new_status: WorkflowStatus) -> None:
        """Transition workflow to a new status."""
        old_status = self.status
        self.status = new_status
        if new_status == WorkflowStatus.COMPLETED:
            self.completed_at = datetime.now()
        logger.info(f"Workflow status transition: {old_status.value} → {new_status.value}")

    def is_ready_for_stage(self, stage: str) -> tuple[bool, Optional[str]]:
        """Check if workflow is ready for a specific stage.

        Returns:
            Tuple of (is_ready, error_message)
        """
        if stage == "scenarios_generation":
            if not self.requirements or not self.requirements.requirements:
                return False, "No requirements available for scenario generation"
            return True, None

        if stage == "test_cases_generation":
            if not self.scenarios or not self.scenarios.scenarios:
                return False, "No scenarios available for test case generation"
            return True, None

        if stage == "validation":
            if not self.test_cases or not self.test_cases.test_cases:
                return False, "No test cases available for validation"
            return True, None

        if stage == "coverage_analysis":
            if not self.test_cases or not self.test_cases.test_cases:
                return False, "No test cases available for coverage analysis"
            return True, None

        if stage == "ui_classification":
            if not self.test_cases or not self.test_cases.test_cases:
                return False, "No test cases available for UI classification"
            return True, None

        if stage == "automation_generation":
            if not self.ui_classifications:
                return False, "No UI classifications available for automation generation"
            return True, None

        return True, None

    def has_critical_errors(self) -> bool:
        """Check if workflow has critical errors that should halt execution."""
        for error in self.errors:
            if error.get("severity") == "critical":
                return True
        return False
