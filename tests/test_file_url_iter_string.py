import pytest
import click
import responses
from click.testing import CliRunner
from click_tools.cli import FileUrlIterStringParamType


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def cli_command():
    """Fixture that provides a Click command using FileUrlIterStringParamType."""
    @click.command()
    @click.argument('input', type=FileUrlIterStringParamType('r'))
    def cmd(input):
        click.echo('\n'.join(line.strip() for line in input))
    return cmd


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("line1\nline2\nline3")
    return f


def test_file_url_iter_string_from_file(cli_runner, cli_command, temp_file):
    """Test FileUrlIterStringParamType reading from a file."""
    result = cli_runner.invoke(cli_command, [str(temp_file)])
    assert result.exit_code == 0
    assert result.output.strip() == 'line1\nline2\nline3'


def test_file_url_iter_string_from_url(cli_runner, cli_command, mock_responses):
    """Test FileUrlIterStringParamType reading from a URL."""
    url = 'http://example.com/data'
    mock_responses.add(
        mock_responses.GET,
        url,
        body=b'line1\nline2\nline3',
        status=200
    )
    
    result = cli_runner.invoke(cli_command, [url])
    assert result.exit_code == 0
    assert result.output.strip() == 'line1\nline2\nline3'


def test_file_url_iter_string_from_string(cli_runner, cli_command):
    """Test FileUrlIterStringParamType with direct string input."""
    result = cli_runner.invoke(cli_command, ['hello'])
    assert result.exit_code == 0
    assert result.output.strip() == 'hello'


def test_file_url_iter_string_from_stdin(cli_runner, cli_command):
    """Test FileUrlIterStringParamType reading from stdin."""
    result = cli_runner.invoke(cli_command, ['-'], input='hello\nworld\n')
    assert result.exit_code == 0
    assert result.output.strip() == 'hello\nworld'


def test_file_url_iter_string_url_error_404(cli_runner, cli_command, mock_responses):
    """Test FileUrlIterStringParamType with URL that returns 404."""
    url = 'http://example.com/error'
    mock_responses.add(
        mock_responses.GET,
        url,
        status=404
    )
    
    result = cli_runner.invoke(cli_command, [url])
    assert result.exit_code != 0
    assert 'not return 200' in result.output


def test_file_url_iter_string_url_error_500(cli_runner, cli_command, mock_responses):
    """Test FileUrlIterStringParamType with URL that returns 500."""
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


def test_file_url_iter_string_url_error_403(cli_runner, cli_command, mock_responses):
    """Test FileUrlIterStringParamType with URL that returns 403."""
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


def test_file_url_iter_string_invalid_mode(cli_runner):
    """Test FileUrlIterStringParamType with invalid mode."""
    param_type = FileUrlIterStringParamType('w')
    with pytest.raises(click.BadParameter) as exc_info:
        param_type.convert('http://example.com', None, None)
    assert 'non-read mode' in str(exc_info.value) 