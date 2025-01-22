import pytest
import click
from click.testing import CliRunner
from click_tools.cli import UrlOrListFromFileStdinParamType


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def cli_command():
    """Fixture that provides a Click command using UrlOrListFromFileStdinParamType."""
    @click.command()
    @click.argument('urls', type=UrlOrListFromFileStdinParamType('r'))
    def cmd(urls):
        if isinstance(urls, list):
            click.echo('\n'.join(urls))
        else:
            for line in urls:
                click.echo(line.strip())
    return cmd


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("http://example.com/1\nhttp://example.com/2")
    return f


def test_url_or_list_single_url(cli_runner, cli_command):
    """Test UrlOrListFromFileStdinParamType with a single URL."""
    result = cli_runner.invoke(cli_command, ['http://example.com'])
    assert result.exit_code == 0
    assert result.output.strip() == 'http://example.com'


def test_url_or_list_from_file(cli_runner, cli_command, temp_file):
    """Test UrlOrListFromFileStdinParamType reading from a file."""
    result = cli_runner.invoke(cli_command, [str(temp_file)])
    assert result.exit_code == 0
    assert 'http://example.com/1' in result.output
    assert 'http://example.com/2' in result.output


def test_url_or_list_from_stdin(cli_runner, cli_command):
    """Test UrlOrListFromFileStdinParamType reading from stdin."""
    result = cli_runner.invoke(cli_command, ['-'], input='http://example.com/1\nhttp://example.com/2\n')
    assert result.exit_code == 0
    assert 'http://example.com/1' in result.output
    assert 'http://example.com/2' in result.output


def test_url_or_list_invalid_url(cli_runner, cli_command):
    """Test UrlOrListFromFileStdinParamType with invalid URL format."""
    result = cli_runner.invoke(cli_command, ['not-a-url'])
    assert result.exit_code != 0  # Should fail since it's not a URL and file doesn't exist


def test_url_or_list_nonexistent_file(cli_runner, cli_command):
    """Test UrlOrListFromFileStdinParamType with nonexistent file."""
    result = cli_runner.invoke(cli_command, ['nonexistent.txt'])
    assert result.exit_code != 0
    assert 'no such file or directory' in result.output.lower() 