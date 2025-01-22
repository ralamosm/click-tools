import os
import pytest
import click
from click.testing import CliRunner
from click_tools.cli import StringOrFileParamType
import tempfile
from unittest.mock import patch, Mock, ANY
from io import StringIO, BytesIO


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def cli_command():
    """Fixture that provides a Click command using StringOrFileParamType."""
    @click.command()
    @click.argument('input', type=StringOrFileParamType('r'))
    def cmd(input):
        click.echo(input.read())
    return cmd


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("test content")
    return f


def test_string_or_file_from_file(cli_runner, cli_command, temp_file):
    """Test StringOrFileParamType reading from a file."""
    result = cli_runner.invoke(cli_command, [str(temp_file)])
    assert result.exit_code == 0
    assert result.output.strip() == "test content"


def test_string_or_file_from_string(cli_runner, cli_command):
    """Test StringOrFileParamType with direct string input."""
    result = cli_runner.invoke(cli_command, ["test content"])
    assert result.exit_code == 0
    assert result.output.strip() == "test content"


class MockTemporaryFile:
    def __init__(self, content, mode='w+'):
        self.name = '/tmp/mock_temp_file'
        self.mode = mode
        self._buffer = StringIO()
        self._content = content
        self._buffer.write(self._content)
        self._buffer.seek(0)
        self._closed = False

    def write(self, data):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        return self._buffer.write(data)

    def read(self, *args, **kwargs):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        self._buffer.seek(0)  # Always read from the start
        return self._buffer.read(*args, **kwargs)

    def flush(self):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        self._buffer.flush()

    def close(self):
        self._closed = True
        self._buffer.close()

    def seek(self, *args, **kwargs):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        self._buffer.seek(*args, **kwargs)

    def tell(self):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        return self._buffer.tell()

    def fileno(self):
        raise OSError("Mock file has no fileno")

    def isatty(self):
        return False

    def readable(self):
        return True

    def writable(self):
        return True

    def seekable(self):
        return True

    @property
    def closed(self):
        return self._closed

    def __enter__(self):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None


def test_string_or_file_cleanup_after_string(cli_runner, cli_command):
    """Test that temporary file is cleaned up after string input."""
    content = "test content"
    mock_temp_file = MockTemporaryFile(content)

    def mock_named_temp_file(**kwargs):
        return mock_temp_file

    def mock_exists(path):
        # Return True only for the temporary file after it's created
        return path == mock_temp_file.name and mock_temp_file._buffer.tell() > 0

    def mock_convert(self, value, param, ctx):
        if value == mock_temp_file.name:
            return mock_temp_file
        return None

    with patch('tempfile.NamedTemporaryFile', side_effect=mock_named_temp_file):
        with patch('os.path.exists', side_effect=mock_exists):
            with patch('os.unlink') as mock_unlink:
                with patch('click.File.convert', mock_convert):
                    result = cli_runner.invoke(cli_command, [content])
                    assert result.exit_code == 0
                    assert result.output.strip() == content
                    mock_unlink.assert_called_once_with(mock_temp_file.name)


def test_string_or_file_from_stdin(cli_runner, cli_command):
    """Test StringOrFileParamType reading from stdin."""
    result = cli_runner.invoke(cli_command, ['-'], input='test content')
    assert result.exit_code == 0
    assert result.output.strip() == "test content"


def test_string_or_file_multiline_string(cli_runner, cli_command):
    """Test StringOrFileParamType with multiline string."""
    content = "line1\nline2\nline3"
    result = cli_runner.invoke(cli_command, [content])
    assert result.exit_code == 0
    assert result.output.strip() == content


def test_string_or_file_empty_string(cli_runner, cli_command):
    """Test StringOrFileParamType with empty string."""
    result = cli_runner.invoke(cli_command, [''])
    assert result.exit_code == 0
    assert result.output.strip() == "" 