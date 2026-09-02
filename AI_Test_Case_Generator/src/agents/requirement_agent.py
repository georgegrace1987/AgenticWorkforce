import sys
from pathlib import Path
from typing import List

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.document_models import DocumentModel
from src.models.requirement_models import RequirementPackage, RequirementModel
from src.orchestration.workflow_state import WorkflowState
from src.orchestration.orchestrator import Agent
import src.llm.model_manager as model_manager
from src.prompts.requirement_prompts import build_requirement_extraction_prompt
from src.utils.logger import get_logger

logger = get_logger("requirement_agent")


class RequirementAgent(Agent):
    """Analyzes normalized documents to extract structured requirements using an LLM.

    This agent uses the configured LLM client to request JSON-formatted
    requirements. If the LLM is unavailable or responses are invalid, the
    agent returns an empty RequirementPackage and logs the issue.
    """

    @property
    def name(self) -> str:
        """Return the agent's name."""
        return "requirement_agent"

    def __init__(self, provider: str | None = None):
        self.client = model_manager.get_llm_client(provider)

    def _fallback_requirements(self, docs: List[DocumentModel]) -> RequirementPackage:
        requirements: List[RequirementModel] = []
        idx = 1
        for doc in docs:
            text_sources = []
            text_sources.extend(p.text for p in (doc.paragraphs or []))
            for table in doc.tables or []:
                if table.headers:
                    text_sources.append(" | ".join(table.headers))
                text_sources.extend(" | ".join(row) for row in table.rows)

            for source_text in text_sources:
                cleaned = source_text.strip()
                if not cleaned:
                    continue
                requirement_id = f"REQ-{idx:03d}"
                requirements.append(
                    RequirementModel(
                        requirement_id=requirement_id,
                        requirement_text=cleaned,
                        requirement_type="Functional",
                        priority="Medium",
                        source_file=doc.filename,
                        source_location="Document content",
                        dependencies=[],
                        business_rules=[],
                        ambiguities=[],
                        assumptions=[],
                    )
                )
                idx += 1
        return RequirementPackage(requirements=requirements, total=len(requirements))

    def analyze_documents(self, docs: List[DocumentModel]) -> RequirementPackage:
        """Analyze a list of DocumentModel objects and return structured requirements."""
        logger.info("Starting requirement analysis for %d documents", len(docs))

        if not self.client.health_check():
            logger.warning("LLM client is unavailable; requirement extraction aborted")
            return self._fallback_requirements(docs)

        # Include both prose and table data because requirements are often tabular.
        summary_parts = []
        for d in docs:
            sections = [p.text for p in (d.paragraphs or [])]
            for table in d.tables or []:
                if table.headers:
                    sections.append(" | ".join(table.headers))
                sections.extend(" | ".join(row) for row in table.rows)
            summary_parts.append(f"Filename: {d.filename}\nContent:\n" + "\n".join(sections))
        prompt = build_requirement_extraction_prompt("\n\n".join(summary_parts))

        # Request structured JSON from the LLM
        try:
            resp = self.client.generate_structured(prompt, schema={})
        except Exception as e:
            logger.exception("LLM call for requirement extraction failed: %s", e)
            return self._fallback_requirements(docs)

        # Expect the client to return JSON-like structure under 'choices' or directly
        raw_requirements = []
        if isinstance(resp, dict):
            # Try common response shapes
            if "choices" in resp and resp["choices"]:
                text = resp["choices"][0].get("message", {}).get("content") or resp["choices"][0].get("text")
                try:
                    import json

                    parsed = json.loads(text)
                    raw_requirements = parsed.get("requirements", []) if isinstance(parsed, dict) else []
                except Exception:
                    logger.debug("Could not parse LLM content as JSON; falling back to empty requirements")
            elif "requirements" in resp:
                raw_requirements = resp.get("requirements") or []

        # Build RequirementModel list safely
        requirements: List[RequirementModel] = []
        for idx, r in enumerate(raw_requirements, start=1):
            try:
                rid = r.get("requirement_id") or f"REQ-{idx:03d}"
                req = RequirementModel(
                    requirement_id=rid,
                    requirement_text=r.get("requirement_text", "Not specified"),
                    requirement_type=r.get("requirement_type", "Not specified"),
                    priority=r.get("priority", "Medium"),
                    source_file=r.get("source_file"),
                    source_location=r.get("source_location"),
                    dependencies=r.get("dependencies", []),
                    business_rules=r.get("business_rules", []),
                    ambiguities=r.get("ambiguities", []),
                    assumptions=r.get("assumptions", []),
                )
                requirements.append(req)
            except Exception:
                logger.exception("Failed to construct RequirementModel for raw item: %s", r)

        pkg = RequirementPackage(requirements=requirements, total=len(requirements))
        if not requirements:
            logger.warning("No structured requirements were returned; using fallback extraction")
            return self._fallback_requirements(docs)
        logger.info("Extracted %d requirements", pkg.total)
        return pkg

    def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the requirement extraction agent on workflow state.

        This method implements the Agent interface, extracting requirements
        from documents in the workflow state and updating the state with results.

        Args:
            state: The current workflow state

        Returns:
            Updated workflow state with requirements extracted
        """
        # Create or get execution record
        record = state.get_agent_record(self.name)
        if record is None:
            record = state.create_agent_record(self.name)

        try:
            record.mark_started()

            # Extract requirements from documents
            requirements = self.analyze_documents(state.documents)

            # Store results in state
            state.requirements = requirements
            state.transition_status(state.status)  # Keep current status

            # Mark as completed
            record.mark_completed()
            logger.info(f"RequirementAgent completed: extracted {len(requirements.requirements)} requirements")

        except Exception as e:
            logger.exception(f"RequirementAgent failed: {e}")
            record.mark_failed(str(e))
            state.add_error(self.name, str(e), severity="critical")

        return state
