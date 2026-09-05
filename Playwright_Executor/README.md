# Playwright Test Case Generator

Automated Playwright test code generation from structured test case definitions.

## Overview

This tool reads test case definitions from JSON files and generates Playwright test code. It provides a structured approach to:

- Define test cases in JSON format
- Auto-generate Playwright test code
- Maintain consistency across test suites
- Enable non-technical team members to create test definitions

## Directory Structure

```
Playwright_Executor/
├── TestCases/                          # Input test case definitions (JSON)
│   ├── sample_test_input.json         # Example test cases
│   └── your_test_cases.json           # Your test case definitions
├── generated_tests/                    # Output directory (auto-created)
│   └── test_*.py                      # Generated Playwright test files
├── playwright_test_generator.py       # Main generator script
└── README.md                           # This file
```

## Quick Start

### 1. Define Test Cases (JSON Format)

Create a JSON file in `TestCases/` folder with your test case definitions:

```json
[
  {
    "test_case_id": "TC001",
    "requirement_id": "REQ001",
    "scenario_id": "SCEN001",
    "title": "User Login with Valid Credentials",
    "test_type": "Functional",
    "priority": "High",
    "preconditions": [
      "Browser is open",
      "User is on login page"
    ],
    "test_data": {
      "username": "testuser@example.com",
      "password": "SecurePassword123"
    },
    "test_steps": [
      {
        "step_number": 1,
        "action": "Enter username in username field",
        "expected": "Username is entered successfully"
      },
      {
        "step_number": 2,
        "action": "Enter password in password field",
        "expected": "Password is masked"
      },
      {
        "step_number": 3,
        "action": "Click Login button",
        "expected": "User is redirected to dashboard"
      }
    ],
    "expected_result": "User is successfully logged in",
    "postconditions": [
      "User session is created"
    ],
    "positive": true,
    "automation_candidate": true
  }
]
```

### 2. Generate Test Code

Run the generator from command line:

```bash
# Basic usage
python playwright_test_generator.py sample_test_input.json

# Custom output filename
python playwright_test_generator.py sample_test_input.json my_tests.py
```

### 3. Implement Test Details

The generated code includes TODO comments where you need to implement:
- Base URLs
- Page object selectors
- Action implementations
- Assertions

Example generated test:

```python
@pytest.mark.high
def test_tc001_user_login_with_valid_credentials(page: Page):
    """
    Test: User Login with Valid Credentials
    
    Test ID: TC001
    Type: Functional
    Priority: High
    """
    BASE_URL = "http://localhost:3000"
    
    # Setup: Preconditions
    # Browser is open
    # User is on login page
    
    # Test Steps
    # Step 1: Enter username in username field
    # Expected: Username is entered successfully
    # TODO: Implement step 1
    # Example patterns:
    # page.goto(f"{BASE_URL}/login")
    # page.fill("#username", "testuser@example.com")
    
    # ... more steps ...
    
    # Verify expected result
    # User is successfully logged in
    # TODO: Add assertion based on expected result
    assert True  # Replace with actual assertion
```

### 4. Run Tests

```bash
# Run all generated tests
pytest -v generated_tests/

# Run specific test file
pytest -v generated_tests/test_sample_test_input.py

# Run tests by priority
pytest -v -m high

# Run specific test
pytest -v generated_tests/test_sample_test_input.py::test_tc001_user_login_with_valid_credentials
```

## Test Case JSON Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `test_case_id` | string | Unique test case identifier (e.g., "TC001") |
| `title` | string | Human-readable test case title |
| `test_steps` | array | Array of test step objects |
| `expected_result` | string | Description of expected result |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `requirement_id` | string | Associated requirement ID |
| `scenario_id` | string | Associated scenario ID |
| `test_type` | string | Type of test (e.g., "Functional", "Regression", "Smoke") |
| `priority` | string | Test priority: "High", "Medium", "Low" (default: "Medium") |
| `preconditions` | array | List of preconditions |
| `postconditions` | array | List of postconditions |
| `test_data` | object | Test data key-value pairs |
| `positive` | boolean | True for positive tests, False for negative tests |
| `automation_candidate` | boolean | Whether test should be automated |
| `boundary_category` | string | Boundary testing category |
| `source_reference` | string | Reference to source document |

### TestStep Object

| Field | Type | Description |
|-------|------|-------------|
| `step_number` | integer | Sequential step number |
| `action` | string | Action to perform |
| `expected` | string | Expected outcome of the action |

## Usage Examples

### Example 1: Basic Login Test

See `TestCases/sample_test_input.json` for a complete example.

### Example 2: Using in Python

```python
from playwright_test_generator import PlaywrightTestGenerator

# Create generator instance
generator = PlaywrightTestGenerator(
    test_cases_dir="TestCases",
    output_dir="generated_tests"
)

# Load and generate tests
generator.generate_and_save("my_test_cases.json")
```

### Example 3: Batch Processing

```python
import json
from pathlib import Path
from playwright_test_generator import PlaywrightTestGenerator

generator = PlaywrightTestGenerator()

# Process all JSON files in TestCases directory
test_cases_dir = Path("TestCases")
for json_file in test_cases_dir.glob("*.json"):
    print(f"Processing {json_file.name}...")
    generator.generate_and_save(json_file.name)
```

## Generated Test Features

Generated tests include:

✓ **Pytest Fixtures** - Browser, context, and page fixtures
✓ **Logging** - Detailed test logging for debugging
✓ **Comments** - Step-by-step comments explaining each test
✓ **Test Data** - Easy access to test data in comments
✓ **Metadata** - Test information (ID, type, priority) in docstrings
✓ **TODOs** - Clear indicators of where implementation is needed
✓ **Example Patterns** - Code examples for common actions

## Requirements

```
playwright>=1.40.0
pytest>=7.0.0
pytest-playwright>=0.4.0
pydantic>=2.0.0
```

Install with:

```bash
pip install -r requirements.txt
```

## Best Practices

1. **Test Case Organization**
   - Group related test cases in separate JSON files
   - Use consistent naming conventions for IDs
   - Keep test_data realistic and representative

2. **Implementation**
   - Replace TODO comments with actual Playwright code
   - Use page object models for complex applications
   - Add proper waits and synchronization

3. **Test Steps**
   - Keep steps atomic and focused
   - Use clear, descriptive action/expected text
   - Limit steps to 5-10 per test case

4. **Test Data**
   - Use realistic test data
   - Avoid hardcoding credentials
   - Consider environment-specific data

5. **Maintenance**
   - Keep JSON definitions in sync with implemented tests
   - Version control test case definitions
   - Review and update regularly

## Troubleshooting

### File Not Found

```
FileNotFoundError: Test case file not found
```

**Solution:** Ensure JSON file is in `TestCases/` directory and path is correct.

### JSON Parse Error

```
json.JSONDecodeError: JSON is malformed
```

**Solution:** Validate JSON format using `json --validate` or online JSON validators.

### Invalid Test Function Name

**Solution:** Ensure test case titles are valid Python identifiers (no special characters).

## Contributing

To extend the generator:

1. Subclass `PlaywrightTestGenerator`
2. Override `_generate_test_function()` for custom test code
3. Add new fixture methods in `_generate_fixtures()`

Example:

```python
class CustomTestGenerator(PlaywrightTestGenerator):
    def _generate_test_function(self, test_case):
        # Custom implementation
        pass
```

## License

[Add your license information]

## Support

For issues, questions, or suggestions, please contact the development team.
