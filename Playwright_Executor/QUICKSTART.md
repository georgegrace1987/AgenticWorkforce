# Playwright Test Generator - Quick Start Guide

## 5-Minute Quick Start

### Step 1: Install Dependencies

```bash
# From Playwright_Executor directory
pip install -r requirements.txt
```

### Step 2: Create Your Test Cases

Create a JSON file in `TestCases/` folder (or use the provided `sample_test_input.json`):

**TestCases/my_login_tests.json:**
```json
[
  {
    "test_case_id": "TC001",
    "requirement_id": "REQ001",
    "scenario_id": "SCEN001",
    "title": "Login with Valid Credentials",
    "test_type": "Functional",
    "priority": "High",
    "preconditions": ["Browser open", "On login page"],
    "test_data": {
      "username": "user@example.com",
      "password": "Password123"
    },
    "test_steps": [
      {
        "step_number": 1,
        "action": "Enter username",
        "expected": "Username displayed"
      },
      {
        "step_number": 2,
        "action": "Enter password",
        "expected": "Password masked"
      },
      {
        "step_number": 3,
        "action": "Click Login",
        "expected": "Redirected to dashboard"
      }
    ],
    "expected_result": "User successfully logged in",
    "postconditions": ["Session created"],
    "positive": true,
    "automation_candidate": true
  }
]
```

### Step 3: Generate Test Code

```bash
# Option 1: Simple generation
python generate_tests.py my_login_tests.json

# Option 2: Specify custom output name
python generate_tests.py my_login_tests.json --output test_my_login.py

# Option 3: Process all JSON files at once
python generate_tests.py --batch

# Option 4: List available test files
python generate_tests.py --list
```

### Step 4: Implement Test Details

Edit the generated test file in `generated_tests/` and fill in the TODO sections:

```python
# Before (generated)
# Step 1: Enter username
# Expected: Username displayed
# TODO: Implement step 1
# Example patterns:
# page.goto(f"{BASE_URL}/login")
# page.fill("#username", "user@example.com")

# After (implemented)
def test_tc001_login_with_valid_credentials(page: Page):
    BASE_URL = "http://localhost:3000"
    
    page.goto(f"{BASE_URL}/login")
    page.fill("#username", "user@example.com")
    page.fill("#password", "Password123")
    page.click("button[type='submit']")
    page.wait_for_url(f"{BASE_URL}/dashboard")
    
    assert page.url == f"{BASE_URL}/dashboard"
```

### Step 5: Run Tests

```bash
# Run all tests
pytest -v generated_tests/

# Run specific file
pytest -v generated_tests/test_my_login_tests.py

# Run by priority
pytest -v -m high

# Run single test
pytest -v generated_tests/test_my_login_tests.py::test_tc001_login_with_valid_credentials

# Run with output
pytest -v -s generated_tests/

# Generate HTML report
pytest --html=report.html generated_tests/
```

## File Reference

| File | Purpose |
|------|---------|
| `playwright_test_generator.py` | Main generator class |
| `generate_tests.py` | Command-line helper script |
| `test_config.py` | Configuration template (customize this) |
| `sample_generated_test.py` | Example of generated code |
| `TestCases/` | Folder for input JSON files |
| `generated_tests/` | Folder for generated Python test files (auto-created) |

## Common Commands

```bash
# Generate from sample
python generate_tests.py sample_test_input.json

# Generate all
python generate_tests.py --batch

# List files
python generate_tests.py --list

# Run all tests
pytest -v generated_tests/

# Run with filtering
pytest -v -k "login"

# Run high priority only
pytest -v -m high

# Show test output
pytest -v -s generated_tests/

# Stop on first failure
pytest -x generated_tests/
```

## Using in Your Code

```python
from playwright_test_generator import PlaywrightTestGenerator

# Generate tests programmatically
gen = PlaywrightTestGenerator()
gen.generate_and_save("my_tests.json", "test_my_suite.py")

# Or with custom directories
gen = PlaywrightTestGenerator(
    test_cases_dir="path/to/testcases",
    output_dir="path/to/output"
)
```

## Tips & Tricks

### 1. Use Page Object Models

```python
class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = "#username"
        self.password_input = "#password"
        self.submit_btn = "button[type='submit']"
    
    def login(self, username, password):
        self.page.fill(self.username_input, username)
        self.page.fill(self.password_input, password)
        self.page.click(self.submit_btn)
```

### 2. Organize Test Data

```python
TEST_DATA = {
    "valid_users": [
        {"username": "user1@test.com", "password": "Pass123"},
        {"username": "user2@test.com", "password": "Pass456"},
    ],
    "invalid_creds": [
        {"username": "bad@test.com", "password": "wrong"},
    ]
}
```

### 3. Use Fixtures for Setup/Teardown

```python
@pytest.fixture
def logged_in_user(page):
    page.goto(BASE_URL + "/login")
    page.fill("#username", "user@test.com")
    page.fill("#password", "Pass123")
    page.click("button[type='submit']")
    page.wait_for_url(BASE_URL + "/dashboard")
    yield page
    # Cleanup
    page.click("#logout")
```

### 4. Add Custom Assertions

```python
def test_layout_responsive(page):
    # Test different viewport sizes
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto(BASE_URL)
    assert page.locator(".navbar").is_visible()
    
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)
    assert page.locator(".mobile-menu").is_visible()
```

## Troubleshooting

### Issue: "Module not found: playwright"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Tests hang or timeout

**Solution:**
```python
page.set_default_timeout(10000)  # 10 seconds
page.goto(BASE_URL, wait_until="networkidle")
```

### Issue: Selectors not found

**Solution:**
1. Check selector in browser DevTools
2. Use `page.pause()` to debug interactively
3. Use explicit waits: `page.wait_for_selector("#element", timeout=5000)`

### Issue: Tests fail in headless mode but pass with GUI

**Solution:**
```python
# Add slow motion for debugging
browser = p.chromium.launch(headless=False, slow_mo=500)
# Or use page.pause() to step through
page.pause()
```

## Next Steps

1. **Customize `test_config.py`** with your selectors and URLs
2. **Create your test cases** in JSON format
3. **Generate test code** using `generate_tests.py`
4. **Implement the TODOs** in generated tests
5. **Run and iterate** - use pytest to run tests
6. **Set up CI/CD** - integrate with your pipeline

## For More Information

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [README.md](README.md) - Comprehensive documentation
