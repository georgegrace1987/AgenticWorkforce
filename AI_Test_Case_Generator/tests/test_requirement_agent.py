import json
from src.agents.requirement_agent import RequirementAgent
from src.models.document_models import DocumentModel, ParagraphModel, SourceLocation
import pytest


class FakeClient:
    last_prompt = ""

    def health_check(self):
        return True

    def generate_structured(self, prompt, schema=None, **kwargs):
        self.last_prompt = prompt
        # Return a structure similar to what an OpenAI-compatible client might return
        return {
            "requirements": [
                {
                    "requirement_id": "REQ-001",
                    "requirement_text": "Users must be able to log in.",
                    "requirement_type": "functional",
                    "priority": "High",
                    "source_file": "sample.docx",
                    "source_location": "paragraph_1",
                    "dependencies": [],
                    "business_rules": [],
                    "ambiguities": [],
                    "assumptions": [],
                }
            ]
        }


@pytest.fixture(autouse=True)
def patch_model_manager(monkeypatch):
    import src.llm.model_manager as mm

    monkeypatch.setattr(mm, "get_llm_client", lambda provider=None: FakeClient())


def test_requirement_agent_basic():
    agent = RequirementAgent()
    doc = DocumentModel(filename="sample.docx", document_type="docx", paragraphs=[ParagraphModel(text="Users must be able to log in.", location=SourceLocation(filename="sample.docx", section="paragraph_1"))])
    pkg = agent.analyze_documents([doc])
    assert pkg.total == 1
    req = pkg.requirements[0]
    assert req.requirement_id == "REQ-001"
    assert "log in" in req.requirement_text.lower()


def test_requirement_agent_includes_table_content():
    agent = RequirementAgent()
    doc = DocumentModel(
        filename="requirements.docx",
        document_type="docx",
        paragraphs=[],
        tables=[
            {
                "headers": ["ID", "Requirement"],
                "rows": [["REQ-001", "Users must be able to export reports."]],
                "location": {"filename": "requirements.docx", "section": "table_1"},
            }
        ],
    )

    agent.analyze_documents([doc])

    assert "Users must be able to export reports." in agent.client.last_prompt


if __name__ == "__main__":
    pytest.main([__file__])
