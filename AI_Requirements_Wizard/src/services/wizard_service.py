import re
from collections.abc import MutableMapping

from src.models.requirements import ChatResponse, RequirementState
from src.llm.provider import ClarificationProvider


class WizardService:
    """Maintain lightweight structured requirement state for a chat session."""

    def __init__(self, sessions: MutableMapping[str, RequirementState], provider: ClarificationProvider | None = None) -> None:
        self.sessions = sessions
        self.provider = provider or ClarificationProvider()

    def process_message(self, session_id: str, message: str) -> ChatResponse:
        state = self.sessions.setdefault(session_id, RequirementState())
        cleaned = " ".join(message.split())
        if self._is_stop_command(cleaned):
            state.questions_paused = True
            state.open_questions = []
        for question in state.open_questions:
            if question not in state.asked_questions:
                state.asked_questions.append(question)
        self._resolve_pending_questions(state, cleaned)
        self._extract(state, message.strip())
        self._record_answered_topics(state, cleaned)
        uses_llm_analysis = hasattr(self.provider, "analyze")
        analysis = self.provider.analyze(state.model_dump(), cleaned) if uses_llm_analysis else {}
        self._merge_llm_requirements(state, analysis.get("requirements", {}))
        questions = [] if state.questions_paused else [str(question).strip() for question in analysis.get("questions", []) if str(question).strip()][:3]
        if not questions and not state.questions_paused and not uses_llm_analysis:
            questions = self.provider.generate_questions(state.model_dump(), cleaned)
        if not questions and not state.questions_paused:
            questions = self._fallback_questions(state, self._readiness_items(state))
        questions = self._remove_answered_questions(state, questions)
        if not questions and not state.questions_paused:
            questions = self._remove_answered_questions(state, self._fallback_questions(state, self._readiness_items(state)))
        state.open_questions = questions
        items = self._readiness_items(state)
        score = round(sum(items.values()) / len(items) * 100)
        self.sessions[session_id] = state
        assistant_message = analysis.get("assistant_message") or self._response(state, questions, score)
        return ChatResponse(
            session_id=session_id,
            assistant_message=assistant_message,
            requirements=state,
            readiness_score=score,
            readiness_items=items,
            open_questions=questions,
        )

    @staticmethod
    def _is_stop_command(message: str) -> bool:
        return message.lower().strip() in {
            "stop asking questions",
            "stop asking",
            "do not ask questions",
            "don't ask questions",
            "no more questions",
        }

    @staticmethod
    def _merge_llm_requirements(state: RequirementState, updates: dict) -> None:
        if not isinstance(updates, dict):
            return
        objective = updates.get("business_objective")
        if objective and not state.business_objective:
            state.business_objective = str(objective).strip()
        for field in ("stakeholders", "user_roles", "functional_requirements", "non_functional_requirements", "technical_requirements", "constraints", "dependencies", "exceptions", "restrictions", "risks", "assumptions"):
            values = updates.get(field) or []
            if not isinstance(values, list):
                continue
            current = getattr(state, field)
            for value in values:
                cleaned = str(value).strip()
                if cleaned and cleaned.lower() != "no information captured" and cleaned not in current:
                    current.append(cleaned)

    @staticmethod
    def _extract(state: RequirementState, message: str) -> None:
        lines = [line.strip(" -*•\t") for line in message.splitlines() if line.strip()]
        if not lines:
            return
        section = ""
        objective_lines = []
        for line in lines:
            lower = line.lower()
            if lower.startswith("1. executive summary") or "executive summary" in lower:
                section = "summary"
                continue
            if lower.startswith("2. requirements overview") or "requirements overview" in lower:
                section = "overview"
                continue
            if lower.startswith("3. user roles") or "user roles" in lower:
                section = "roles"
                continue
            if lower.startswith("4. constraints") or "constraints and risks" in lower:
                section = "constraints"
                continue
            if lower.startswith("5. assumptions") or "assumptions" in lower:
                section = "assumptions"
                continue
            if lower.startswith("6. open issues") or "open issues" in lower:
                section = "issues"
                continue
            if lower in {"functional requirements", "id | requirement", "id", "requirement"}:
                continue
            if lower.startswith("non-functional requirements"):
                section = "nonfunctional"
                continue

            requirement_match = re.match(r"(?:FR|NFR)-?\d+\s*[|:\t-]\s*(.+)", line, re.IGNORECASE)
            value = requirement_match.group(1).strip() if requirement_match else line
            if not requirement_match:
                roles = re.findall(r"(?:users?|customers?|admins?|employees?|supervisors?|managers?|staff)", lower)
                for role in roles:
                    if role not in state.user_roles:
                        state.user_roles.append(role)
                if lower.startswith("users:") or lower.startswith("user roles:"):
                    listed_roles = re.split(r",|\band\b|/", line.split(":", 1)[1], flags=re.IGNORECASE)
                    for role in listed_roles:
                        role = role.strip(" -*•\t.").lower()
                        if role and role not in state.user_roles:
                            state.user_roles.append(role)
            if requirement_match:
                if line.upper().startswith("NFR"):
                    if value not in state.non_functional_requirements:
                        state.non_functional_requirements.append(value)
                elif value not in state.functional_requirements:
                    state.functional_requirements.append(value)
            elif section == "summary":
                objective_lines.append(value)
            elif section == "roles":
                role = value.lower()
                if role and role not in state.user_roles and role not in {"no information captured"}:
                    state.user_roles.append(role)
            elif section == "nonfunctional" or any(word in lower for word in ("secure", "security", "fast", "performance", "availability", "access control", "professional", "usability", "user experience", "ui", "interface")):
                if value not in state.non_functional_requirements and value.lower() != "no information captured":
                    state.non_functional_requirements.append(value)
            elif section == "constraints":
                if value.lower() != "no information captured" and value not in state.constraints:
                    state.constraints.append(value)
            elif section == "assumptions" and value.lower() != "no information captured":
                if value not in state.assumptions:
                    state.assumptions.append(value)
            elif section == "issues" and value.lower() != "no information captured":
                if value not in state.open_questions:
                    state.open_questions.append(value)
            elif any(word in lower for word in ("fill", "check", "analyze", "complexity", "level", "generate")):
                if value not in state.functional_requirements:
                    state.functional_requirements.append(value)
            elif any(word in lower for word in ("python", "web based", "web-based", "database", "api", "framework", "architecture", "hosting", "browser")):
                if value not in state.technical_requirements:
                    state.technical_requirements.append(value)
            elif requirement_match or any(word in lower for word in ("must", "should", "allow", "enable", "can ", "will have", "access", "read/write", "add", "update", "delete", "dashboard", "report")):
                if value not in state.functional_requirements:
                    state.functional_requirements.append(value)

        if state.business_objective is None:
            state.business_objective = " ".join(objective_lines) if objective_lines else lines[0]

    @staticmethod
    def _readiness_items(state: RequirementState) -> dict[str, bool]:
        return {
            "Business objective": bool(state.business_objective),
            "Users and roles": bool(state.user_roles) or "users" in state.answered_topics,
            "Core workflows": bool(state.functional_requirements) or "workflow" in state.answered_topics,
            "Quality expectations": "quality" in state.answered_topics or bool(state.non_functional_requirements),
            "Constraints and risks": "constraints" in state.answered_topics or bool(state.constraints or state.risks),
        }

    @staticmethod
    def _resolve_pending_questions(state: RequirementState, message: str) -> None:
        lower = message.lower().strip().rstrip(".!?")
        if not state.open_questions:
            return
        skip_answer = (
            lower in {"skip", "skipped", "not specified", "not sure", "unknown", "no information", "no other requirements"}
            or lower.startswith("skip ")
            or "proceed with document" in lower
        )
        no_requirements = lower == "no other requirements"
        if skip_answer:
            for topic in ("users", "workflow", "quality", "constraints", "exceptions", "technical"):
                if topic not in state.answered_topics:
                    state.answered_topics.append(topic)
        if no_requirements:
            for topic in ("users", "workflow", "quality", "constraints"):
                if topic not in state.answered_topics:
                    state.answered_topics.append(topic)
        for question in state.open_questions:
            question_lower = question.lower()
            if any(term in question_lower for term in ("security", "performance", "availability")):
                if lower in {"no", "none", "nope", "not at this time", "nothing specific"} or skip_answer:
                    if "quality" not in state.answered_topics:
                        state.answered_topics.append("quality")
            if any(term in question_lower for term in ("limit", "policy", "constraint", "integration")):
                if lower in {"no", "none", "nope", "not at this time"} or skip_answer:
                    if "constraints" not in state.answered_topics:
                        state.answered_topics.append("constraints")
            if skip_answer and any(term in question_lower for term in ("workflow", "must support", "process")):
                if "workflow" not in state.answered_topics:
                    state.answered_topics.append("workflow")
            if skip_answer and any(term in question_lower for term in ("who will", "users", "roles")):
                if "users" not in state.answered_topics:
                    state.answered_topics.append("users")
        state.open_questions = []

    @staticmethod
    def _remove_answered_questions(state: RequirementState, questions: list[str]) -> list[str]:
        topic_terms = {
            "users": ("who will", "users", "roles"),
            "workflow": ("workflow", "must support", "process"),
            "quality": ("security", "performance", "availability"),
            "constraints": ("limit", "policy", "constraint", "integration"),
            "technical": ("technical", "stack", "runtime", "framework", "deployment", "data store", "hosting"),
            "exceptions": ("error", "invalid", "exception", "failure", "validation"),
        }
        filtered = []
        for question in questions:
            lower = question.lower()
            if question in state.asked_questions:
                continue
            if any(topic in state.answered_topics and any(term in lower for term in terms) for topic, terms in topic_terms.items()):
                continue
            if question not in filtered:
                filtered.append(question)
        return filtered[:3]

    @staticmethod
    def _record_answered_topics(state: RequirementState, message: str) -> None:
        topic_words = {
            "users": ("user", "customer", "admin", "role", "staff"),
            "workflow": ("must", "should", "allow", "enable", "workflow", "transfer", "view"),
            "quality": ("secure", "security", "fast", "performance", "availability", "available"),
            "constraints": ("limit", "constraint", "only", "except", "cannot", "must not"),
            "technical": ("python", "web", "database", "api", "framework", "hosting", "browser", "architecture"),
            "exceptions": ("error", "invalid", "exception", "failure", "fails", "validation"),
        }
        lower = message.lower()
        for topic, words in topic_words.items():
            if any(word in lower for word in words) and topic not in state.answered_topics:
                state.answered_topics.append(topic)

    @staticmethod
    def _fallback_questions(state: RequirementState, items: dict[str, bool]) -> list[str]:
        """Ask only about the topics shown in the readiness checklist.

        Keeping fallback questions aligned with `_readiness_items` prevents the
        readiness score from reaching 100% while unresolved questions remain,
        which is what disables the Generate SRD button in the UI.
        """
        questions: list[str] = []
        if not items["Users and roles"]:
            questions.append(WizardService._fresh_question(state, "Who will use the system, and what roles should they have?", "Which people or teams need access, and what should each role be able to do?"))
        if not items["Core workflows"]:
            questions.append(WizardService._fresh_question(state, "What is the most important workflow the system must support?", "What should a user be able to accomplish from start to finish?"))
        if not items["Quality expectations"]:
            questions.append(WizardService._fresh_question(state, "Are there security, performance, or availability expectations?", "What standards should the product meet for security, speed, reliability, or usability?"))
        if not items["Constraints and risks"]:
            questions.append(WizardService._fresh_question(state, "Are there important limits, policies, or integrations to consider?", "Does the solution need to follow any policies, connect to other systems, or work within known limits?"))
        return questions[:3]

    @staticmethod
    def _fresh_question(state: RequirementState, primary: str, alternative: str) -> str:
        return alternative if primary in state.asked_questions else primary

    @staticmethod
    def _response(state: RequirementState, questions: list[str], score: int) -> str:
        captured = len(state.functional_requirements) + len(state.non_functional_requirements)
        objective = state.business_objective or "this product idea"
        roles = ", ".join(state.user_roles[:3]) if state.user_roles else "the relevant users"
        if state.functional_requirements:
            workflow_summary = state.functional_requirements[0]
        elif state.user_roles:
            workflow_summary = f"core access and workflow needs for {roles}"
        else:
            workflow_summary = "the core product workflow"

        if questions:
            next_question = questions[0]
            assumption = "I’m assuming the main priority is role-based access and a clear workflow unless you tell me otherwise."
            if state.non_functional_requirements:
                assumption = "I’m assuming the quality bar is driven by security, usability, and reliability unless you want to prioritize something else."
            return (
                f"I’ve captured the core of this brief: {objective}. "
                f"I’m hearing that {workflow_summary} matters most, with {roles} as the key stakeholders. "
                f"{assumption} The next decision I need is: {next_question}"
            )

        return (
            f"The brief is coming together. I’ve captured {captured} structured requirement(s) and the current readiness is {score}%. "
            f"I’m comfortable with the direction for {objective}, and the remaining work is mainly refining the workflow and quality expectations before we generate the SRD."
        )
