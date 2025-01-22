import pytest
import click
from click_tools.cli import ListCommaSeparated


@pytest.fixture
def cli_command():
    """Fixture that provides a Click command using ListCommaSeparated."""
    @click.command()
    @click.option('--tags', type=ListCommaSeparated())
    def cmd(tags):
        click.echo(','.join(tags) if tags else '')
    return cmd


def test_list_comma_separated_single_value():
    """Test ListCommaSeparated with a single value."""
    param_type = ListCommaSeparated()
    result = param_type.convert('a', None, None)
    assert result == ['a']


def test_list_comma_separated_multiple_values():
    """Test ListCommaSeparated with multiple values."""
    param_type = ListCommaSeparated()
    result = param_type.convert('a,b,c', None, None)
    assert set(result) == {'a', 'b', 'c'}


def test_list_comma_separated_duplicates():
    """Test ListCommaSeparated with duplicate values."""
    param_type = ListCommaSeparated()
    result = param_type.convert('a,b,a', None, None)
    assert len(result) == 2
    assert set(result) == {'a', 'b'}


def test_list_comma_separated_allow_duplicates():
    """Test ListCommaSeparated with duplicates allowed."""
    param_type = ListCommaSeparated()
    param_type.unique = False  # Set after initialization
    result = param_type.convert('a,b,a', None, None)
    assert sorted(result) == sorted(['a', 'b', 'a'])


def test_list_comma_separated_empty():
    """Test ListCommaSeparated with empty input."""
    param_type = ListCommaSeparated()
    result = param_type.convert('', None, None)
    assert result == []


def test_list_comma_separated_whitespace():
    """Test ListCommaSeparated with whitespace."""
    param_type = ListCommaSeparated()
    result = param_type.convert(' a , b , c ', None, None)
    assert set(result) == {'a', 'b', 'c'}


def test_list_comma_separated_list_input():
    """Test ListCommaSeparated with list input."""
    param_type = ListCommaSeparated()
    result = param_type.convert(['a', 'b', 'c'], None, None)
    assert set(result) == {'a', 'b', 'c'} 