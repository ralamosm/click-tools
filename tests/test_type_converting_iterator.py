import pytest

from click_tools import TypeConvertingIterator


def test_type_converting_iterator_with_conversion():
    """Test TypeConvertingIterator with a conversion function."""
    iterator = TypeConvertingIterator(['1', '2', '3'], int)
    assert list(iterator) == [1, 2, 3]


def test_type_converting_iterator_without_conversion():
    """Test TypeConvertingIterator without a conversion function."""
    data = ['a', 'b', 'c']
    iterator = TypeConvertingIterator(data, None)
    assert list(iterator) == data


def test_type_converting_iterator_empty():
    """Test TypeConvertingIterator with an empty iterator."""
    with pytest.raises(StopIteration):
        TypeConvertingIterator([], int)


def test_type_converting_iterator_invalid_conversion():
    """Test TypeConvertingIterator with an invalid conversion."""
    with pytest.raises(ValueError):
        TypeConvertingIterator(['not a number'], int)


def test_type_converting_iterator_repr():
    """Test the string representation of TypeConvertingIterator."""
    iterator = TypeConvertingIterator(['1', '2'], int)
    assert 'TypeConvertingIterator' in repr(iterator)
    assert str(int) in repr(iterator) 