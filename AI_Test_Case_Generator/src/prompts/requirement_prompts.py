from typing import Any


def build_requirement_extraction_prompt(document_summary: str) -> str:
    """Construct a prompt asking the LLM to extract structured requirements.

    The prompt requests JSON output with a top-level `requirements` array containing
    objects with fields required by `RequirementModel`.
    """
    prompt = (
        "You are an assistant that extracts functional and non-functional requirements "
        "from software requirement documents.\n"
        "Return a single valid JSON object with a top-level key `requirements` which is an array. "
        "Each requirement object must include: requirement_id, requirement_text, requirement_type, "
        "priority, source_file, source_location, dependencies (list), business_rules (list), ambiguities (list), assumptions (list).\n"
        "If a field is missing, use the string 'Not specified' or an empty list where appropriate.\n"
        "Do NOT invent requirements that are not present in the source. If information is ambiguous or missing, mark it accordingly.\n\n"
        "Document summary:\n" + document_summary + "\n\nReturn only JSON."
    )
    return prompt
