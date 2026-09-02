from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from src.orchestration.workflow_state import WorkflowState
from src.utils.logger import get_logger

logger = get_logger("orchestrator")


class Agent(ABC):
    """Base class for all workflow agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique agent name."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, state: WorkflowState) -> WorkflowState:
        """Perform work against the current workflow state."""
        raise NotImplementedError


class AgentOrchestrator:
    """Coordinates execution of multiple agents over a shared WorkflowState."""

    def __init__(self, state_dir: Optional[str | Path] = None):
        project_root = Path(__file__).resolve().parents[2]
        self.state_dir = Path(state_dir) if state_dir else project_root / "data" / "workflows"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.agents: Dict[str, Agent] = {}
        self.agent_order: List[str] = []

    def register_agent(self, agent: Agent) -> None:
        """Register a new agent in the workflow."""
        if not isinstance(agent, Agent):
            raise TypeError("Expected an Agent instance")

        if agent.name in self.agents:
            logger.warning("Agent already registered: %s", agent.name)
            return

        self.agents[agent.name] = agent
        self.agent_order.append(agent.name)
        logger.info("Registered agent: %s", agent.name)

    def unregister_agent(self, agent_name: str) -> None:
        """Remove an agent from the workflow."""
        self.agents.pop(agent_name, None)
        if agent_name in self.agent_order:
            self.agent_order.remove(agent_name)

    def _state_file_for(self, workflow_id: str) -> Path:
        return self.state_dir / f"{workflow_id}.json"

    def save_state(self, state: WorkflowState) -> Path:
        """Persist a workflow state to disk."""
        file_path = self._state_file_for(state.workflow_id)
        payload = state.model_dump(mode="json")
        file_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        logger.info("Saved workflow state: %s -> %s", state.workflow_id, file_path)
        return file_path

    def load_state(self, workflow_id: str) -> WorkflowState:
        """Load a workflow state from disk by workflow ID."""
        file_path = self._state_file_for(workflow_id)
        if not file_path.exists():
            raise FileNotFoundError(f"No workflow state found for ID: {workflow_id}")

        data = json.loads(file_path.read_text(encoding="utf-8"))
        return WorkflowState.model_validate(data)

    def list_workflows(self) -> List[str]:
        """Return all workflow IDs currently saved on disk."""
        return sorted(p.stem for p in self.state_dir.glob("*.json"))

    def _get_resume_index(self, state: WorkflowState) -> int:
        """Return the first agent not yet completed successfully."""
        completed_agents = {
            record.agent_name
            for record in state.agent_history
            if record.status == "success"
        }
        for idx, agent_name in enumerate(self.agent_order):
            if agent_name not in completed_agents:
                return idx
        return len(self.agent_order)

    def execute(
        self,
        state: WorkflowState,
        fail_on_error: bool = True,
        start_index: int = 0,
    ) -> WorkflowState:
        """Execute all registered agents sequentially on the workflow state."""
        logger.info("Starting workflow execution: %s", state.workflow_id)
        logger.info("Total agents: %d, starting at index: %d", len(self.agents), start_index)

        for idx, agent_name in enumerate(self.agent_order[start_index:], start=start_index):
            agent = self.agents.get(agent_name)
            if agent is None:
                continue

            record = state.get_agent_record(agent.name)
            if record is None:
                record = state.create_agent_record(agent.name)

            logger.info("Executing agent: %s", agent.name)
            try:
                record.mark_started()
                state = agent.execute(state)
            except Exception as exc:
                record.mark_failed(str(exc))
                logger.exception("Agent failed: %s", agent.name)
                state.add_error(agent.name, str(exc), severity="critical")
                if fail_on_error:
                    raise
                break

            if state is None:
                raise RuntimeError(f"Agent {agent.name} returned None")

            record.mark_completed()
            self.save_state(state)
            logger.info("Agent completed: %s", agent.name)

        logger.info("Workflow execution finished: %s", state.workflow_id)
        return state

    def resume_workflow(self, workflow_id: str, fail_on_error: bool = False) -> WorkflowState:
        """Reload state and continue execution from the next unfinished agent."""
        state = self.load_state(workflow_id)
        start_index = self._get_resume_index(state)
        logger.info("Resuming workflow %s from agent index %d", workflow_id, start_index)
        return self.execute(state, fail_on_error=fail_on_error, start_index=start_index)