import click
import pytest
from click.testing import CliRunner
from click_tools.cli import FileIterStringParamType


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("")  # Create empty file
    return f


@pytest.fixture
def cli_command():
    @click.command()
    @click.argument('numbers', type=FileIterStringParamType('r', type=int))
    def cmd(numbers):
        for num in numbers:
            click.echo(str(num))
    return cmd


def test_file_iter_string_from_file(cli_runner, temp_file):
    """Test FileIterStringParamType reading from a file."""
    temp_file.write_text('1\n2\n3')
    
    @click.command()
    @click.argument('input', type=FileIterStringParamType('r'))
    def cmd(input):
        click.echo('\n'.join(line.strip() for line in input))

    result = cli_runner.invoke(cmd, [str(temp_file)])
    assert result.exit_code == 0
    assert result.output.strip() == '1\n2\n3'


def test_file_iter_string_with_conversion(cli_runner, temp_file):
    """Test FileIterStringParamType with type conversion."""
    temp_file.write_text('1\n2\n3')
    
    @click.command()
    @click.argument('numbers', type=FileIterStringParamType('r', type=int))
    def cmd(numbers):
        total = sum(numbers)
        click.echo(str(total))

    result = cli_runner.invoke(cmd, [str(temp_file)])
    assert result.exit_code == 0
    assert result.output.strip() == '6'


def test_file_iter_string_from_string(cli_runner):
    """Test FileIterStringParamType with direct string input."""
    @click.command()
    @click.argument('numbers', type=FileIterStringParamType('r', type=int))
    def cmd(numbers):
        for num in numbers:
            click.echo(str(num))

    result = cli_runner.invoke(cmd, ['42'])
    assert result.exit_code == 0
    assert result.output.strip() == '42'


def test_file_iter_string_from_stdin(cli_runner):
    """Test FileIterStringParamType reading from stdin."""
    @click.command()
    @click.argument('numbers', type=FileIterStringParamType('r', type=int))
    def cmd(numbers):
        total = sum(numbers)
        click.echo(str(total))

    result = cli_runner.invoke(cmd, ['-'], input='1\n2\n3\n')
    assert result.exit_code == 0
    assert result.output.strip() == '6'


def test_file_iter_string_invalid_conversion(cli_runner):
    """Test FileIterStringParamType with invalid type conversion."""
    @click.command()
    @click.argument('numbers', type=FileIterStringParamType('r', type=int))
    def cmd(numbers):
        click.echo('\n'.join(numbers))

    result = cli_runner.invoke(cmd, ['not-a-number'])
    assert result.exit_code != 0


def test_file_iter_string_invalid_mode(cli_runner):
    """Test FileIterStringParamType with invalid mode."""
    with pytest.raises(click.BadParameter):
        FileIterStringParamType('w').convert('test.txt', None, None) 