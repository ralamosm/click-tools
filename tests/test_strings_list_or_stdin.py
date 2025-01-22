import pytest
import click

from click_tools import StringsListOrStdinParamType


@pytest.fixture
def cli_command():
    """Fixture that provides a Click command using StringsListOrStdinParamType."""
    @click.command()
    @click.argument('input', type=StringsListOrStdinParamType())
    def cmd(input):
        if hasattr(input, 'read'):
            click.echo(input.read().strip())
        else:
            click.echo(','.join(input))
    return cmd


def test_strings_list_or_stdin_direct_string(cli_runner, cli_command):
    """Test StringsListOrStdinParamType with a direct string input."""
    result = cli_runner.invoke(cli_command, ['hello'])
    assert result.exit_code == 0
    assert result.output.strip() == 'hello'


def test_strings_list_or_stdin_from_stdin(cli_runner, cli_command):
    """Test StringsListOrStdinParamType reading from stdin."""
    result = cli_runner.invoke(cli_command, ['-'], input='hello\nworld\n')
    assert result.exit_code == 0
    assert result.output.strip() == 'hello\nworld'


def test_strings_list_or_stdin_list_input(cli_runner, cli_command):
    """Test StringsListOrStdinParamType with list input."""
    param_type = StringsListOrStdinParamType()
    result = param_type.convert(['a', 'b', 'c'], None, None)
    assert result == ['a', 'b', 'c']


def test_strings_list_or_stdin_empty_string():
    """Test StringsListOrStdinParamType with empty string."""
    param_type = StringsListOrStdinParamType()
    result = param_type.convert('', None, None)
    assert result == [''] 