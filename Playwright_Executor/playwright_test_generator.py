"""
Playwright Test Generator

This module generates Playwright test cases from JSON input files.
It reads test case definitions and generates corresponding Playwright test code.
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightTestGenerator:
    """Generate Playwright test code from test case definitions."""

    def __init__(self, test_cases_dir: str = None, output_dir: str = None):
        """
        Initialize the test generator.
        
        Args:
            test_cases_dir: Directory containing test case JSON files
            output_dir: Directory to write generated test files
        """
        base_dir = Path(__file__).parent
        self.test_cases_dir = Path(test_cases_dir) if test_cases_dir else base_dir / "TestCases"
        self.output_dir = Path(output_dir) if output_dir else base_dir / "generated_tests"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_test_cases(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load test cases from a JSON file.
        
        Args:
            filename: Name of the JSON file (with or without .json extension)
            
        Returns:
            List of test case dictionaries
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = self.test_cases_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Test case file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            return json.load(f)

    def generate_test_code(self, test_cases: List[Dict[str, Any]]) -> str:
        """
        Generate Playwright test code from test cases.
        
        Args:
            test_cases: List of test case dictionaries
            
        Returns:
            Generated test code as string
        """
        code = self._generate_header()
        code += self._generate_imports()
        code += self._generate_fixtures()
        
        for test_case in test_cases:
            code += self._generate_test_function(test_case)
        
        return code

    def _generate_header(self) -> str:
        """Generate file header with metadata."""
        return f'''"""
Playwright Tests

Auto-generated from test case definitions.
Generated: {datetime.now().isoformat()}

Usage:
    pytest -v test_*.py
    pytest -k <test_name>
"""

'''

    def _generate_imports(self) -> str:
        """Generate import statements."""
        return '''import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import logging
from typing import Generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''

    def _generate_fixtures(self) -> str:
        """Generate pytest fixtures."""
        return '''
@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Fixture to initialize browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Fixture to create a new browser context."""
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Fixture to create a new page."""
    page = context.new_page()
    yield page
    page.close()


'''

    def _generate_test_function(self, test_case: Dict[str, Any]) -> str:
        """
        Generate a test function for a single test case.
        
        Args:
            test_case: Test case dictionary
            
        Returns:
            Test function code as string
        """
        test_id = test_case.get('test_case_id', 'UNKNOWN')
        title = test_case.get('title', 'Untitled Test')
        priority = test_case.get('priority', 'Medium')
        test_type = test_case.get('test_type', 'Functional')
        
        # Generate test function name from title
        test_func_name = self._title_to_function_name(test_id, title)
        
        # Start building test code
        code = f'''
@pytest.mark.{priority.lower()}
def {test_func_name}(page: Page):
    """
    Test: {title}
    
    Test ID: {test_id}
    Type: {test_type}
    Priority: {priority}
    """
    logger.info(f"Starting test: {test_id} - {title}")
    
    # TODO: Set the correct base URL
    BASE_URL = "http://localhost:3000"
'''
        
        # Add preconditions
        preconditions = test_case.get('preconditions', [])
        if preconditions:
            code += self._generate_preconditions(preconditions)
        
        # Add test steps
        test_steps = test_case.get('test_steps', [])
        if test_steps:
            code += self._generate_test_steps(test_steps, test_case)
        
        # Add expected result verification
        expected_result = test_case.get('expected_result', '')
        if expected_result:
            code += f'''
    # Verify expected result
    # {expected_result}
    # TODO: Add assertion based on expected result
    assert True  # Replace with actual assertion
'''
        
        # Add postconditions
        postconditions = test_case.get('postconditions', [])
        if postconditions:
            code += self._generate_postconditions(postconditions)
        
        code += f'''
    logger.info(f"Test passed: {test_id}")

'''
        return code

    def _title_to_function_name(self, test_id: str, title: str) -> str:
        """Convert test title to valid Python function name."""
        # Use test_id as base, append sanitized title
        name = f"test_{test_id.lower()}".replace('-', '_')
        
        # Add sanitized title words
        title_words = title.lower().split()[:3]  # Take first 3 words
        for word in title_words:
            # Remove non-alphanumeric characters
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word:
                name += f"_{clean_word}"
        
        return name

    def _generate_preconditions(self, preconditions: List[str]) -> str:
        """Generate precondition setup code."""
        code = '''
    # Setup: Preconditions
'''
        for precond in preconditions:
            code += f'''    # {precond}
'''
        code += '''
'''
        return code

    def _generate_test_steps(self, test_steps: List[Dict[str, str]], test_case: Dict[str, Any]) -> str:
        """Generate test step code."""
        code = '''
    # Test Steps
'''
        test_data = test_case.get('test_data', {})
        
        for step in test_steps:
            step_num = step.get('step_number', 0)
            action = step.get('action', '')
            expected = step.get('expected', '')
            
            code += f'''
    # Step {step_num}: {action}
    # Expected: {expected}
    # TODO: Implement step {step_num}
    # Example patterns:
    # page.goto(f"{{BASE_URL}}/login")
    # page.fill("#username", "{test_data.get('username', 'value')}")
    # page.fill("#password", "{test_data.get('password', 'value')}")
    # page.click("#login-button")
    # page.wait_for_url(f"{{BASE_URL}}/dashboard")

'''
        
        return code

    def _generate_postconditions(self, postconditions: List[str]) -> str:
        """Generate postcondition cleanup code."""
        code = '''
    # Cleanup: Postconditions
'''
        for postcond in postconditions:
            code += f'''    # {postcond}
'''
        code += '''
'''
        return code

    def generate_and_save(self, input_filename: str, output_filename: str = None) -> str:
        """
        Load test cases and generate test file.
        
        Args:
            input_filename: Input JSON file name
            output_filename: Output test file name (auto-generated if not provided)
            
        Returns:
            Path to generated test file
        """
        test_cases = self.load_test_cases(input_filename)
        test_code = self.generate_test_code(test_cases)
        
        if output_filename is None:
            # Generate output filename from input filename
            base_name = Path(input_filename).stem
            output_filename = f"test_{base_name}.py"
        
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w') as f:
            f.write(test_code)
        
        logger.info(f"Generated test file: {output_path}")
        return str(output_path)


def main():
    """Main function for command-line usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python playwright_test_generator.py <input_file.json> [output_file.py]")
        print("\nExample:")
        print("  python playwright_test_generator.py sample_test_input.json")
        print("  python playwright_test_generator.py sample_test_input.json my_custom_tests.py")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    generator = PlaywrightTestGenerator()
    
    try:
        generated_path = generator.generate_and_save(input_file, output_file)
        print(f"✓ Test file generated successfully: {generated_path}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
