import pytest
import click
from click.testing import CliRunner

from click_tools import ChoiceCommaSeparated


@pytest.fixture
def choices():
    """Fixture that provides a list of choices for testing."""
    return ['apple', 'banana', 'orange']


@pytest.fixture
def cli_command(choices):
    """Fixture that provides a Click command using ChoiceCommaSeparated."""
    @click.command()
    @click.option('--fruits', type=ChoiceCommaSeparated(choices))
    def cmd(fruits):
        click.echo(','.join(fruits) if fruits else '')
    return cmd


def test_choice_comma_separated_single_value(cli_runner, cli_command):
    """Test ChoiceCommaSeparated with a single valid value."""
    result = cli_runner.invoke(cli_command, ['--fruits', 'apple'])
    assert result.exit_code == 0
    assert result.output.strip() == 'apple'


def test_choice_comma_separated_multiple_values(cli_runner, cli_command):
    """Test ChoiceCommaSeparated with multiple valid values."""
    result = cli_runner.invoke(cli_command, ['--fruits', 'apple,banana'])
    assert result.exit_code == 0
    assert result.output.strip() == 'apple,banana'


def test_choice_comma_separated_invalid_value(cli_runner, cli_command):
    """Test ChoiceCommaSeparated with an invalid value."""
    result = cli_runner.invoke(cli_command, ['--fruits', 'grape'])
    assert result.exit_code != 0
    assert 'is not a valid choice' in result.output


def test_choice_comma_separated_wildcard(cli_runner, cli_command, choices):
    """Test ChoiceCommaSeparated with wildcard."""
    result = cli_runner.invoke(cli_command, ['--fruits', '*'])
    assert result.exit_code == 0
    assert all(choice in result.output for choice in choices)


def test_choice_comma_separated_case_insensitive():
    """Test ChoiceCommaSeparated with case insensitive option."""
    param_type = ChoiceCommaSeparated(['Apple', 'Banana'], case_sensitive=False)
    result = param_type.convert('Apple,Banana', None, None)
    assert result == ['Apple', 'Banana']
    
    # Test that case-insensitive comparison works
    with pytest.raises(click.BadParameter):
        param_type.convert('apple,banana', None, None)


def test_choice_comma_separated_no_wildcard():
    """Test ChoiceCommaSeparated with wildcard disabled."""
    param_type = ChoiceCommaSeparated(['apple', 'banana'], allow_wildcard=False)
    with pytest.raises(click.BadParameter):
        param_type.convert('*', None, None)


def test_choice_comma_separated_empty():
    """Test ChoiceCommaSeparated with empty input."""
    param_type = ChoiceCommaSeparated(['apple', 'banana'])
    result = param_type.convert('', None, None)
    assert result == []


def test_choice_comma_separated_whitespace():
    """Test ChoiceCommaSeparated with whitespace in input."""
    param_type = ChoiceCommaSeparated(['apple', 'banana'])
    result = param_type.convert(' apple , banana ', None, None)
    assert result == ['apple', 'banana'] 