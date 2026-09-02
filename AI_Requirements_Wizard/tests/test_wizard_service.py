from src.models.requirements import RequirementState
from src.services.wizard_service import WizardService


class FakeClarificationProvider:
    def generate_questions(self, state, message):
        return ["Which payment provider should the portal integrate with?"]


def test_questions_are_generated_by_provider() -> None:
    service = WizardService({}, provider=FakeClarificationProvider())

    response = service.process_message("session-1", "Customers can view invoices.")

    assert response.open_questions == ["Which payment provider should the portal integrate with?"]
    assert response.readiness_score == 60


def test_assistant_message_feels_agentic_and_summary_driven() -> None:
    service = WizardService({})

    response = service.process_message("session-agentic", "Customers can view invoices.")

    assert "I’m hearing" in response.assistant_message or "I’ve captured" in response.assistant_message
    assert "please clarify" not in response.assistant_message.lower()
    assert "1." not in response.assistant_message


def test_provider_question_is_not_repeated() -> None:
    service = WizardService({}, provider=FakeClarificationProvider())

    service.process_message("session-repeat", "Customers can view invoices.")
    response = service.process_message("session-repeat", "Stripe")

    assert response.open_questions != ["Which payment provider should the portal integrate with?"]


def test_fallback_questions_do_not_repeat_answered_topics() -> None:
    service = WizardService({})

    first = service.process_message("session-2", "Customers can view invoices.")
    second = service.process_message("session-2", "Customers must log in securely.")

    assert "Are there security, performance, or availability expectations?" in first.open_questions
    assert "Are there security, performance, or availability expectations?" not in second.open_questions


def test_negative_answer_resolves_pending_quality_question() -> None:
    service = WizardService({})

    service.process_message("session-3", "Customers can view invoices.")
    response = service.process_message("session-3", "No")

    assert "quality" in response.requirements.answered_topics
    assert "Are there security, performance, or availability expectations?" not in response.open_questions
    assert response.readiness_score == 100


def test_skip_advances_past_all_current_questions() -> None:
    service = WizardService({})

    first = service.process_message("session-skip", "Customers can view invoices.")
    response = service.process_message("session-skip", "Skip")

    assert not set(response.open_questions).intersection(first.open_questions)
    assert "workflow" in response.requirements.answered_topics
    assert "quality" in response.requirements.answered_topics
    assert "constraints" in response.requirements.answered_topics


def test_conversation_extracts_roles_access_and_quality_requirements() -> None:
    service = WizardService({})

    service.process_message("session-detail", "We need an internal customer account portal.")
    service.process_message("session-detail", "Users: Admin, Employee, Supervisor")
    service.process_message(
        "session-detail",
        "Admin will have full access. Employee can read/write. Supervisor can read/write and view dashboards.",
    )
    response = service.process_message("session-detail", "User based access control is priority. UI needs to be professional.")

    assert {"admin", "employee", "supervisor"}.issubset(response.requirements.user_roles)
    assert response.requirements.non_functional_requirements
    assert response.readiness_items["Quality expectations"]
    assert response.requirements.functional_requirements