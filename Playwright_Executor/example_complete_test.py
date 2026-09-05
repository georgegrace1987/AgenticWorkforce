"""
Playwright Tests - Complete Implementation Example

This file shows a fully implemented test based on the generator output.
It's a real-world example you can use as a reference for implementing your own tests.
"""

import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import logging
from typing import Generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://demo.example.com"  # Replace with your app URL
TIMEOUT = 10000  # 10 seconds


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Fixture to initialize browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            slow_mo=100,  # Add 100ms delay to see what's happening
        )
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
    page.set_default_timeout(TIMEOUT)
    yield page
    page.close()


# Page Object Model - LoginPage
class LoginPage:
    """Page object for login page."""
    
    def __init__(self, page: Page):
        self.page = page
        # Selectors for login page
        self.username_input = "#username"
        self.password_input = "#password"
        self.login_button = "button[type='submit']"
        self.error_message = ".alert-danger"
        self.success_message = ".alert-success"
    
    def goto(self):
        """Navigate to login page."""
        self.page.goto(f"{BASE_URL}/login")
    
    def fill_username(self, username: str):
        """Fill username field."""
        self.page.fill(self.username_input, username)
    
    def fill_password(self, password: str):
        """Fill password field."""
        self.page.fill(self.password_input, password)
    
    def click_login(self):
        """Click login button."""
        self.page.click(self.login_button)
    
    def login(self, username: str, password: str):
        """Complete login flow."""
        self.fill_username(username)
        self.fill_password(password)
        self.click_login()
    
    def has_error(self) -> bool:
        """Check if error message is displayed."""
        try:
            self.page.wait_for_selector(self.error_message, timeout=3000)
            return True
        except:
            return False
    
    def has_success(self) -> bool:
        """Check if success message is displayed."""
        try:
            self.page.wait_for_selector(self.success_message, timeout=3000)
            return True
        except:
            return False


# Page Object Model - DashboardPage
class DashboardPage:
    """Page object for dashboard page."""
    
    def __init__(self, page: Page):
        self.page = page
        self.navbar = "nav.navbar"
        self.logout_button = "#logout"
        self.user_name = ".user-name"
    
    def is_loaded(self) -> bool:
        """Check if dashboard is loaded."""
        try:
            self.page.wait_for_selector(self.navbar, timeout=5000)
            return True
        except:
            return False
    
    def get_username(self) -> str:
        """Get displayed username."""
        return self.page.text_content(self.user_name)
    
    def logout(self):
        """Click logout button."""
        self.page.click(self.logout_button)


# Test Cases

@pytest.mark.high
@pytest.mark.smoke
def test_tc001_login_with_valid_credentials(page: Page):
    """
    Test: User Login with Valid Credentials
    
    Test ID: TC001
    Type: Functional
    Priority: High
    
    This test verifies that a user can successfully login with valid credentials.
    """
    logger.info("Starting test: TC001 - Login with Valid Credentials")
    
    # Setup
    login_page = LoginPage(page)
    login_page.goto()
    
    # Verify we're on login page
    assert "login" in page.url.lower()
    logger.info("✓ Successfully navigated to login page")
    
    # Execute: Login with valid credentials
    test_username = "testuser@example.com"
    test_password = "SecurePassword123"
    
    login_page.login(test_username, test_password)
    logger.info("✓ Submitted login form")
    
    # Verify: Dashboard is displayed
    dashboard_page = DashboardPage(page)
    assert dashboard_page.is_loaded(), "Dashboard failed to load"
    logger.info("✓ Dashboard loaded successfully")
    
    # Verify: User info is displayed
    displayed_username = dashboard_page.get_username()
    assert test_username in displayed_username or displayed_username, \
        f"Expected username to be displayed, got: {displayed_username}"
    logger.info(f"✓ User info displayed: {displayed_username}")
    
    # Cleanup
    dashboard_page.logout()
    logger.info("✓ Logged out successfully")
    
    logger.info("✓ Test passed: TC001")


@pytest.mark.high
@pytest.mark.smoke
def test_tc002_login_with_invalid_credentials(page: Page):
    """
    Test: User Login with Invalid Credentials
    
    Test ID: TC002
    Type: Functional
    Priority: High
    
    This test verifies that login fails with invalid credentials and shows error.
    """
    logger.info("Starting test: TC002 - Login with Invalid Credentials")
    
    # Setup
    login_page = LoginPage(page)
    login_page.goto()
    
    assert "login" in page.url.lower()
    logger.info("✓ Navigated to login page")
    
    # Execute: Attempt login with invalid credentials
    login_page.login("wrong@example.com", "WrongPassword123")
    logger.info("✓ Submitted login form with invalid credentials")
    
    # Verify: Error message is displayed
    assert login_page.has_error(), "Expected error message not displayed"
    logger.info("✓ Error message displayed")
    
    # Verify: Still on login page
    assert "login" in page.url.lower()
    logger.info("✓ Remained on login page after failed login")
    
    logger.info("✓ Test passed: TC002")


@pytest.mark.medium
def test_tc003_password_field_is_masked(page: Page):
    """
    Test: Password Field is Masked
    
    Test ID: TC003
    Type: Functional
    Priority: Medium
    
    This test verifies that password input is masked for security.
    """
    logger.info("Starting test: TC003 - Password Field is Masked")
    
    # Setup
    login_page = LoginPage(page)
    login_page.goto()
    
    # Get password input element
    password_input = page.query_selector(login_page.password_input)
    
    # Execute: Fill password
    password_text = "TestPassword123"
    login_page.fill_password(password_text)
    logger.info("✓ Entered password")
    
    # Verify: Password field type is "password" (masked)
    input_type = password_input.get_attribute("type")
    assert input_type == "password", f"Expected type='password', got type='{input_type}'"
    logger.info("✓ Password field is of type 'password' (masked)")
    
    # Verify: Value is not visible as plain text (depends on browser behavior)
    # Note: Direct value access may not show the actual text due to security
    logger.info("✓ Test passed: TC003")


@pytest.mark.low
def test_tc004_login_page_elements_visible(page: Page):
    """
    Test: Login Page Elements are Visible
    
    Test ID: TC004
    Type: Smoke/UI
    Priority: Low
    
    This test verifies that all required elements on login page are visible.
    """
    logger.info("Starting test: TC004 - Login Page Elements Visible")
    
    # Setup
    login_page = LoginPage(page)
    login_page.goto()
    
    # Verify all elements are visible
    elements_to_check = [
        (login_page.username_input, "Username input"),
        (login_page.password_input, "Password input"),
        (login_page.login_button, "Login button"),
    ]
    
    for selector, name in elements_to_check:
        element = page.query_selector(selector)
        assert element is not None, f"{name} not found"
        assert element.is_visible(), f"{name} not visible"
        logger.info(f"✓ {name} is visible")
    
    logger.info("✓ Test passed: TC004")


@pytest.mark.parametrize("username,password,should_succeed", [
    ("validuser@example.com", "ValidPassword123", True),
    ("testuser@example.com", "TestPassword123", True),
    ("invalid@example.com", "WrongPassword", False),
    ("", "", False),
])
@pytest.mark.high
def test_tc005_login_parametrized(page: Page, username: str, password: str, should_succeed: bool):
    """
    Test: Parametrized Login Test
    
    Test ID: TC005
    Type: Functional
    Priority: High
    
    This test uses parametrize to test multiple login scenarios.
    """
    logger.info(f"Testing login with: username={username}, should_succeed={should_succeed}")
    
    # Setup
    login_page = LoginPage(page)
    login_page.goto()
    
    # Execute: Attempt login
    login_page.login(username, password)
    logger.info("✓ Submitted login form")
    
    # Verify based on expected result
    if should_succeed:
        dashboard_page = DashboardPage(page)
        assert dashboard_page.is_loaded(), "Dashboard should have loaded"
        logger.info("✓ Login succeeded as expected")
        dashboard_page.logout()
    else:
        assert login_page.has_error(), "Error message should be displayed"
        logger.info("✓ Login failed as expected")
    
    logger.info(f"✓ Test passed: TC005")


# Run tests with: pytest -v example_complete_test.py
# Run specific test: pytest -v example_complete_test.py::test_tc001_login_with_valid_credentials
# Run by marker: pytest -v -m high example_complete_test.py
# Run with output: pytest -v -s example_complete_test.py
