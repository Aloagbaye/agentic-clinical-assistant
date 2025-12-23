"""Example test file to verify test setup."""

import pytest


def test_example():
    """Example test to verify pytest is working."""
    assert True


def test_import_package():
    """Test that the package can be imported."""
    import agentic_clinical_assistant
    
    assert agentic_clinical_assistant.__version__ == "0.1.0"

