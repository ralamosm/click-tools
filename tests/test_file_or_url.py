import pytest
import click
import responses
import os
from click.testing import CliRunner
from click_tools.cli import FileOrUrlParamType
import tempfile
from unittest.mock import patch, Mock, ANY
from io import StringIO, BytesIO


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def cli_command():
    """Fixture that provides a Click command using FileOrUrlParamType."""
    @click.command()
    @click.argument('input', type=FileOrUrlParamType('r'))
    def cmd(input):
        click.echo(input.read())
    return cmd


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("test content")
    return f


def test_file_or_url_from_file(cli_runner, cli_command, temp_file):
    """Test FileOrUrlParamType reading from a file."""
    result = cli_runner.invoke(cli_command, [str(temp_file)])
    assert result.exit_code == 0
    assert result.output.strip() == "test content"


def test_file_or_url_from_url(cli_runner, cli_command, mock_responses):
    """Test FileOrUrlParamType reading from a URL."""
    url = 'http://example.com/test'
    content = 'url content'
    mock_responses.add(
        mock_responses.GET,
        url,
        body=content
    )

    result = cli_runner.invoke(cli_command, [url])
    assert result.exit_code == 0
    assert result.output.strip() == content


def test_file_or_url_url_error_404(cli_runner, cli_command, mock_responses):
    """Test FileOrUrlParamType with URL that returns 404."""
    url = 'http://example.com/error'
    mock_responses.add(
        mock_responses.GET,
        url,
        body='Not Found',
        status=404
    )

    result = cli_runner.invoke(cli_command, [url])
    assert result.exit_code != 0
    assert 'not return 200' in result.output


def test_file_or_url_url_error_500(cli_runner, cli_command, mock_responses):
    """Test FileOrUrlParamType with URL that returns 500."""
    url = 'http://example.com/error'
    mock_responses.add(
        mock_responses.GET,
        url,
        body='Server Error',
        status=500
    )

    result = cli_runner.invoke(cli_command, [url])
    assert result.exit_code != 0
    assert 'not return 200' in result.output


def test_file_or_url_url_error_403(cli_runner, cli_command, mock_responses):
    """Test FileOrUrlParamType with URL that returns 403."""
    url = 'http://example.com/error'
    mock_responses.add(
        mock_responses.GET,
        url,
        body='Forbidden',
        status=403
    )

    result = cli_runner.invoke(cli_command, [url])
    assert result.exit_code != 0
    assert 'not return 200' in result.output


class MockTemporaryFile:
    def __init__(self, content, mode='wb+'):
        self.name = '/tmp/mock_temp_file'
        self.mode = mode
        self._buffer = BytesIO()
        self._content = content.encode('utf-8') if isinstance(content, str) else content
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
        if 'b' in self.mode:
            return self._buffer.read(*args, **kwargs)
        else:
            return self._buffer.read(*args, **kwargs).decode('utf-8')

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


def test_file_or_url_cleanup_after_url(cli_runner, cli_command, mock_responses):
    """Test that temporary file is cleaned up after URL download."""
    url = 'http://example.com/test'
    content = 'url content'
    mock_responses.add(
        mock_responses.GET,
        url,
        body=content
    )

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
                    result = cli_runner.invoke(cli_command, [url])
                    assert result.exit_code == 0
                    assert result.output.strip() == content
                    mock_unlink.assert_called_once_with(mock_temp_file.name)


def test_file_or_url_invalid_mode(cli_runner):
    """Test FileOrUrlParamType with invalid mode."""
    param_type = FileOrUrlParamType('w')
    with pytest.raises(click.BadParameter) as exc_info:
        param_type.convert('http://example.com', None, None)
    assert 'non-read mode' in str(exc_info.value)


def test_file_or_url_nonexistent_file(cli_runner, cli_command):
    """Test FileOrUrlParamType with nonexistent file."""
    result = cli_runner.invoke(cli_command, ['nonexistent.txt'])
    assert result.exit_code != 0
    assert 'no such file or directory' in result.output.lower() 