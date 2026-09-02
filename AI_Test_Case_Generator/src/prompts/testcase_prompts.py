def build_testcase_generation_prompt(requirement_summary: str) -> str:
    return (
        "You are an expert QA analyst helping convert requirements into test scenarios and test cases.\n"
        "Return a single valid JSON object with these top-level keys:\n"
        "- requirements_outline: array of short bullet strings summarizing the document requirements\n"
        "- scenarios: array of scenario objects\n"
        "- test_cases: array of test case objects\n\n"
        "Scenario object fields: scenario_id, requirement_id, scenario_title, scenario_description, scenario_type, priority, rationale, source_reference.\n"
        "Test case object fields: test_case_id, requirement_id, scenario_id, title, test_type, priority, preconditions (list), test_data (object), test_steps (list of objects with step_number, action, expected), expected_result, postconditions (list), positive (bool), boundary_category, automation_candidate (bool), source_reference.\n"
        "Use the provided requirement ids where available. Do not invent unsupported business logic. If something is missing, use 'Not specified' or an empty list/object.\n"
        "Keep scenarios and test cases concise but complete.\n\n"
        f"Requirements summary:\n{requirement_summary}\n\n"
        "Return only JSON."
    )
