import os
import tempfile
from pathlib import Path

import pytest
import responses
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Fixture that provides a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_file():
    """Fixture that provides a temporary file that is cleaned up after the test."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        temp_path = f.name
        yield f
        
    # Clean up the file after the test
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_file_with_content(temp_file):
    """Fixture that provides a temporary file with some content."""
    content = "line1\nline2\nline3\n"
    temp_file.write(content)
    temp_file.flush()
    return temp_file


@pytest.fixture
def mock_responses():
    """Fixture that provides a responses object for mocking HTTP requests."""
    with responses.RequestsMock() as rsps:
        yield rsps 