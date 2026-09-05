"""
Configuration template for Playwright tests.

Copy this file and customize for your application.
"""

# Base URLs for different environments
BASE_URLS = {
    "dev": "http://localhost:3000",
    "staging": "https://staging.example.com",
    "production": "https://www.example.com",
}

# Common selectors (page object model approach)
SELECTORS = {
    "login": {
        "username_field": "#username",
        "password_field": "#password",
        "login_button": "button[type='submit']",
        "error_message": ".alert-danger",
        "welcome_message": ".welcome",
    },
    "dashboard": {
        "navbar": "nav.navbar",
        "logout_button": "#logout",
        "user_menu": ".user-menu",
    },
    "registration": {
        "first_name": "#firstName",
        "last_name": "#lastName",
        "email": "#email",
        "password": "#password",
        "confirm_password": "#confirmPassword",
        "submit_button": "button[type='submit']",
    },
}

# Default timeouts (in milliseconds)
TIMEOUTS = {
    "short": 3000,      # Quick element interactions
    "medium": 10000,    # Page loads
    "long": 30000,      # Large data loads
}

# Default browser options
BROWSER_OPTIONS = {
    "headless": True,
    "slow_mo": 0,  # Slow motion in milliseconds (useful for debugging)
}

# Retry configuration
RETRY = {
    "max_retries": 3,
    "wait_between_retries": 1000,  # milliseconds
}

# Logging configuration
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# Test data
TEST_DATA = {
    "valid_users": [
        {"username": "testuser@example.com", "password": "ValidPassword123"},
        {"username": "admin@example.com", "password": "AdminPassword123"},
    ],
    "invalid_credentials": [
        {"username": "testuser@example.com", "password": "WrongPassword"},
        {"username": "nonexistent@example.com", "password": "AnyPassword"},
    ],
    "boundary_values": {
        "max_username_length": 255,
        "min_password_length": 8,
        "max_password_length": 128,
    },
}

# Environment to use (dev, staging, production)
CURRENT_ENV = "dev"

# Get current base URL
def get_base_url():
    """Get base URL for current environment."""
    return BASE_URLS.get(CURRENT_ENV, BASE_URLS["dev"])


# Get selector by page and element name
def get_selector(page: str, element: str):
    """Get CSS selector for given page and element."""
    try:
        return SELECTORS[page][element]
    except KeyError:
        raise ValueError(f"Selector not found: {page}.{element}")
