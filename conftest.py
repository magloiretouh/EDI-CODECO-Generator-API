"""
Pytest configuration and shared fixtures for test suite.
"""

import pytest
import asyncio
from pathlib import Path


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests at session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def cleanup_output_dir():
    """Cleanup test output directory before and after tests."""
    test_output = Path('./test_output')

    # Cleanup before test
    if test_output.exists():
        import shutil
        shutil.rmtree(test_output)

    yield

    # Cleanup after test
    if test_output.exists():
        import shutil
        shutil.rmtree(test_output)
