from typing import List
from src.models.document_models import DocumentModel
from src.models.requirement_models import RequirementPackage
from src.agents.requirement_agent import RequirementAgent


class RequirementService:
    """Service layer for requirement extraction; separates agent usage from API/UI code."""

    def __init__(self, provider: str | None = None):
        self.agent = RequirementAgent(provider=provider)

    def extract_requirements(self, docs: List[DocumentModel]) -> RequirementPackage:
        return self.agent.analyze_documents(docs)
