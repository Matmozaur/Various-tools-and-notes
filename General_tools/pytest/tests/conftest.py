import pytest
from src.calculator import Calculator


@pytest.fixture
def calculator():
    """Fixture to provide a Calculator instance."""
    return Calculator()


@pytest.fixture(scope="module")
def setup_module():
    """Runs once per test module (example: database connection)."""
    print("\n[Setup] Initializing Module")
    yield
    print("\n[Teardown] Cleaning Up Module")
