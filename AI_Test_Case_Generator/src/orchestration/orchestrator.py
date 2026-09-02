"""Agent orchestration framework for the AI Test Case Generator.

This module provides the AgentOrchestrator class which manages the
execution of agents in the correct order, maintains workflow state,
handles errors, and provides checkpoints for resumability.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod

from src.orchestration.workflow_state import WorkflowState, WorkflowStatus, AgentExecutionRecord
from src.utils.logger import get_logger

logger = get_logger("orchestrator")


class Agent(ABC):
    """Abstract base class for agents in the orchestration pipeline."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's name."""
        raise NotImplementedError()

    @abstractmethod
    def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the agent and return updated state.

        The agent should:
        1. Get or create its execution record
        2. Mark itself as started
        3. Perform its work
        4. Update state with results
        5. Mark itself as completed or failed
        """
        raise NotImplementedError()


class AgentOrchestrator:
    """Orchestrates the execution of agents in the agentic workflow.

    Features:
    - Registers agents and their execution order
    - Executes agents sequentially with state management
    - Tracks agent execution history and metrics
    - Handles errors and recovery
    - Persists workflow state
    - Provides resumability
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """Initialize the orchestrator.

        Args:
            state_dir: Directory to persist workflow state. If None,
                      uses in-memory state only.
        """
        self.agents: List[Agent] = []
        self.agent_map: Dict[str, Agent] = {}
        self.state_dir = Path(state_dir) if state_dir else None
        if self.state_dir:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Workflow state will be persisted to: {self.state_dir}")
        else:
            logger.info("Workflow state is in-memory only (not persistent)")

    def register_agent(self, agent: Agent) -> None:
        """Register an agent for orchestration.

        Agents are executed in the order they are registered.

        Args:
            agent: An instance of a class implementing the Agent interface
        """
        self.agents.append(agent)
        self.agent_map[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    def register_agents(self, *agents: Agent) -> None:
        """Register multiple agents at once."""
        for agent in agents:
            self.register_agent(agent)

    def _get_state_file(self, workflow_id: str) -> Path:
        """Get the path for a workflow state file."""
        if not self.state_dir:
            raise ValueError("State persistence is not enabled")
        return self.state_dir / f"{workflow_id}.json"

    def save_state(self, state: WorkflowState) -> None:
        """Persist workflow state to disk."""
        if not self.state_dir:
            logger.debug("State persistence disabled; skipping save")
            return

        try:
            state_file = self._get_state_file(state.workflow_id)
            state_json = state.model_dump_json(indent=2)
            state_file.write_text(state_json)
            logger.info(f"Workflow state persisted: {state_file}")
        except Exception as e:
            logger.error(f"Failed to persist workflow state: {e}")

    def load_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Load workflow state from disk.

        Args:
            workflow_id: The workflow ID to load

        Returns:
            WorkflowState if found, None otherwise
        """
        if not self.state_dir:
            logger.debug("State persistence disabled; cannot load state")
            return None

        try:
            state_file = self._get_state_file(workflow_id)
            if not state_file.exists():
                logger.debug(f"No persisted state found: {state_file}")
                return None

            state_json = state_file.read_text()
            state_dict = json.loads(state_json)
            state = WorkflowState(**state_dict)
            logger.info(f"Workflow state loaded: {state_file}")
            return state
        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return None

    def execute(
        self,
        initial_state: WorkflowState,
        skip_agents: Optional[List[str]] = None,
        fail_on_error: bool = True,
    ) -> WorkflowState:
        """Execute the workflow using registered agents.

        Args:
            initial_state: The starting workflow state
            skip_agents: List of agent names to skip (e.g., for recovery)
            fail_on_error: If True, halt on first error. If False, collect errors.

        Returns:
            Updated WorkflowState after all agents execute
        """
        state = initial_state
        skip_set = set(skip_agents or [])

        logger.info(f"Starting workflow execution: {state.workflow_id}")
        logger.info(f"Total agents: {len(self.agents)}, Skipping: {len(skip_set)}")

        for agent in self.agents:
            if agent.name in skip_set:
                logger.info(f"Skipping agent (on skip list): {agent.name}")
                continue

            # Check if workflow is ready for this agent
            stage = self._get_stage_for_agent(agent.name)
            is_ready, error_msg = state.is_ready_for_stage(stage)
            if not is_ready:
                logger.warning(f"Agent {agent.name} preconditions not met: {error_msg}")
                state.add_warning(agent.name, f"Preconditions not met: {error_msg}")
                if fail_on_error:
                    state.add_error(agent.name, error_msg, severity="critical")
                    state.transition_status(WorkflowStatus.FAILED)
                    self.save_state(state)
                    raise RuntimeError(f"Workflow failed: {error_msg}")
                continue

            # Execute agent
            logger.info(f"Executing agent: {agent.name}")
            try:
                state = agent.execute(state)
                record = state.get_agent_record(agent.name)
                if record:
                    logger.info(
                        f"Agent completed: {agent.name} "
                        f"(duration: {record.duration_ms}ms, status: {record.status})"
                    )
                    if record.warnings:
                        for warning in record.warnings:
                            state.add_warning(agent.name, warning)

            except Exception as e:
                logger.exception(f"Agent failed with exception: {agent.name}")
                state.add_error(agent.name, str(e), severity="critical")
                record = state.get_agent_record(agent.name)
                if record:
                    record.mark_failed(str(e))
                state.transition_status(WorkflowStatus.FAILED)
                self.save_state(state)
                if fail_on_error:
                    raise
                else:
                    # Continue with next agent despite error
                    continue

            # Check for errors in state
            if state.has_critical_errors():
                logger.error("Workflow has critical errors; halting execution")
                state.transition_status(WorkflowStatus.FAILED)
                self.save_state(state)
                if fail_on_error:
                    raise RuntimeError("Workflow has critical errors")
                else:
                    break

            # Persist state checkpoint
            self.save_state(state)

        # Mark workflow as completed
        if state.status != WorkflowStatus.FAILED:
            state.transition_status(WorkflowStatus.COMPLETED)
            self.save_state(state)
            logger.info(f"Workflow completed successfully: {state.workflow_id}")
        else:
            logger.error(f"Workflow failed: {state.workflow_id}")

        return state

    def _get_stage_for_agent(self, agent_name: str) -> str:
        """Map agent name to workflow stage."""
        stage_map = {
            "requirement_agent": "requirements_analysis",
            "scenario_agent": "scenarios_generation",
            "test_case_agent": "test_cases_generation",
            "validation_agent": "validation",
            "coverage_agent": "coverage_analysis",
            "ui_classifier_agent": "ui_classification",
            "playwright_agent": "automation_generation",
        }
        return stage_map.get(agent_name, "unknown")

    def get_execution_summary(self, state: WorkflowState) -> Dict[str, Any]:
        """Get a summary of workflow execution."""
        return state.get_execution_summary()

    def resume_workflow(
        self,
        workflow_id: str,
        from_agent: Optional[str] = None,
        fail_on_error: bool = True,
    ) -> Optional[WorkflowState]:
        """Resume a previously saved workflow.

        Args:
            workflow_id: The workflow ID to resume
            from_agent: Agent to resume from. If None, resumes from last failed agent.
            fail_on_error: If True, halt on first error. If False, collect errors.

        Returns:
            Updated WorkflowState, or None if workflow not found
        """
        state = self.load_state(workflow_id)
        if not state:
            logger.error(f"Cannot resume: workflow not found {workflow_id}")
            return None

        logger.info(f"Resuming workflow: {workflow_id}")
        logger.info(f"Current status: {state.status}")

        # Determine which agents to skip
        skip_agents = []
        if from_agent:
            # Skip all agents before the specified one
            for agent in self.agents:
                if agent.name == from_agent:
                    break
                skip_agents.append(agent.name)
        else:
            # Skip all agents that have already completed successfully
            for record in state.agent_history:
                if record.status == "success":
                    skip_agents.append(record.agent_name)

        logger.info(f"Skipping {len(skip_agents)} previously completed agents")

        # Reset status to allow resumption
        state.transition_status(WorkflowStatus.RECEIVED)

        # Execute with skips
        return self.execute(state, skip_agents=skip_agents, fail_on_error=fail_on_error)

    def list_workflows(self) -> List[str]:
        """List all persisted workflow IDs.

        Returns:
            List of workflow IDs found in the state directory
        """
        if not self.state_dir:
            return []

        workflow_ids = []
        for state_file in self.state_dir.glob("*.json"):
            workflow_ids.append(state_file.stem)
        return sorted(workflow_ids)
