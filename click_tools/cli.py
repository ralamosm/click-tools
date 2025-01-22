import itertools
import tempfile
from os.path import exists

import click
import requests
import validators


class TypeConvertingIterator:
    """An iterator that applies a type conversion function to each element.

    This iterator wraps another iterator and applies a conversion function to each element
    as it is yielded. It also validates that the first element can be converted before
    allowing iteration to proceed.

    Args:
        iterator: The source iterator whose elements will be converted
        conversion_function: A callable that takes one argument and returns the converted value.
            If None, elements are returned as-is.

    Raises:
        Any exception that the conversion_function might raise when converting the first element.

    Example:
        >>> numbers = TypeConvertingIterator(['1', '2', '3'], int)
        >>> list(numbers)
        [1, 2, 3]
    """

    def __init__(self, iterator, conversion_function=None):
        self.iterator = iterator
        self.conversion_function = conversion_function
        self._check_convertibility()

    def __iter__(self):
        return self

    def __next__(self):
        return self.conversion_function(next(self.iterator)) if self.conversion_function is not None else next(self.iterator)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.iterator.__repr__()}, {self.conversion_function})"

    def _check_convertibility(self):
        """Validates that the first element can be converted using the conversion function.
        
        This method creates a tee of the iterator to check the first element without consuming
        the original iterator. If the conversion fails, the error will be raised immediately
        rather than waiting until the first element is requested.
        """
        tee_iterator, self.iterator = itertools.tee(self.iterator)
        try:
            first = next(tee_iterator)
            if self.conversion_function is not None:
                self.conversion_function(first)
        except StopIteration:
            # Re-raise StopIteration to indicate empty iterator
            raise


class ChoiceCommaSeparated(click.ParamType):
    """A Click parameter type that handles comma-separated values and validates them against choices.

    This parameter type splits the input string on commas and validates each value against
    a predefined set of choices. It supports wildcards to select all choices and can be
    configured for case sensitivity.

    Args:
        choices: List of valid choices to validate against
        allow_wildcard: If True, allows '*' or 'all' to select all choices. Defaults to True.
        case_sensitive: If True, validates choices with case sensitivity. Defaults to True.

    Example:
        >>> @click.command()
        >>> @click.option('--fruits', type=ChoiceCommaSeparated(['apple', 'banana']))
        >>> def cmd(fruits):
        ...     print(fruits)
        >>> # Valid inputs:
        >>> # --fruits "apple,banana"
        >>> # --fruits "*"  # If allow_wildcard=True
    """

    name = "choice-comma-separated"

    def __init__(self, choices, *args, **kwargs):
        self.choices = choices
        self.allow_wildcard = kwargs.get("allow_wildcard", True)
        self.case_sensitive = kwargs.get("case_sensitive", True)

        if "allow_wildcard" in kwargs:
            del kwargs["allow_wildcard"]
        if "case_sensitive" in kwargs:
            del kwargs["case_sensitive"]

        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        """Convert and validate the command-line value.

        Args:
            value: The command-line value to convert
            param: The parameter being processed
            ctx: The Click context

        Returns:
            List of validated choices

        Raises:
            click.BadParameter: If any value is not in the valid choices
        """
        if not value:
            return []

        if not isinstance(value, list):
            value = [ss.strip() for ss in value.split(",")]

        if self.allow_wildcard:
            if any(val in ("*", "all") for val in value):
                return self.choices

        for val in value:
            if self.case_sensitive:
                if val.lower() not in [cc.lower() for cc in self.choices]:
                    self.fail("Value {} is not a valid choice.".format(val))
            else:
                if val not in self.choices:
                    self.fail("Value {} is not a valid choice.".format(val))

        return value


class ListCommaSeparated(click.ParamType):
    """A Click parameter type that converts comma-separated strings into a list.

    This parameter type splits the input on commas and optionally ensures uniqueness
    of the resulting values.

    Args:
        unique: If True, removes duplicates from the resulting list. Defaults to True.

    Example:
        >>> @click.command()
        >>> @click.option('--tags', type=ListCommaSeparated())
        >>> def cmd(tags):
        ...     print(tags)
        >>> # Input: --tags "a,b,c"
        >>> # Output: ['a', 'b', 'c']
    """

    name = "list-comma-separated"

    def __init__(self, *args, **kwargs):
        self.unique = kwargs.get("unique", True)
        super().__init__(*args, **kwargs)

    def convert(self, value, *args):
        """Convert the command-line value into a list.

        Args:
            value: The command-line value to convert

        Returns:
            List of strings, optionally deduplicated
        """
        if not value:
            return []

        if not isinstance(value, list):
            lista = [ss.strip() for ss in value.split(",")]
        else:
            lista = value

        if self.unique:
            lista = list(set(lista))

        return lista


class StringsListOrStdinParamType(click.ParamType):
    """A Click parameter type that accepts either a string value or reads from stdin.

    This parameter type allows flexibility in input sources, accepting either a direct
    string value or reading from standard input when '-' is provided.

    Example:
        >>> @click.command()
        >>> @click.argument('input', type=StringsListOrStdinParamType())
        >>> def cmd(input):
        ...     for line in input:
        ...         print(line)
        >>> # Valid inputs:
        >>> # "direct string"
        >>> # - (reads from stdin)
    """

    name = "strings-list-or-stdin"

    def convert(self, value, param, ctx):
        """Convert the input value to either a stream or a list.

        Args:
            value: The command-line value to convert
            param: The parameter being processed
            ctx: The Click context

        Returns:
            Either a text stream (if value is '-') or a single-item list
        """
        if value == "-":
            return click.get_text_stream("stdin")
        else:
            if isinstance(value, str):
                return [value]
            else:
                return value


class FileUrlIterStringParamType(click.File):
    """A Click parameter type that handles files, URLs, and direct strings as iterators.

    This versatile parameter type can handle multiple input sources:
    - Local files (using Click's File type)
    - URLs (streaming the response)
    - Standard input (using '-')
    - Direct strings (converted to single-item iterators)

    Example:
        >>> @click.command()
        >>> @click.argument('input', type=FileUrlIterStringParamType('r'))
        >>> def cmd(input):
        ...     for line in input:
        ...         print(line)
        >>> # Valid inputs:
        >>> # file.txt
        >>> # http://example.com
        >>> # "direct string"
        >>> # - (stdin)
    """

    def convert(self, value, param, ctx):
        """Convert the input value to an appropriate iterator.

        Args:
            value: The command-line value to convert
            param: The parameter being processed
            ctx: The Click context

        Returns:
            An iterator over the input source

        Raises:
            click.BadParameter: If the file can't be opened in read mode or URL fetch fails
        """
        if "r" not in self.mode:
            self.fail("stream cannot be opened in non-read mode", param, ctx)

        if exists(value):
            # value is a valid filename
            f = super().convert(value, param, ctx)
            return iter(f)
        elif validators.url(value):
            # value is a url
            try:
                r = requests.get(value)
                if not r.ok:
                    self.fail("Url %s does not return 200 OK" % value, param, ctx)
            except Exception as e:
                self.fail("Error while fetching %s: %s" % (value, e), param, ctx)

            # Convert bytes to string and split into lines
            content = r.content.decode('utf-8') if isinstance(r.content, bytes) else r.content
            return iter(content.splitlines())
        elif value == "-":
            # value is stdin
            return click.get_text_stream("stdin")
        else:
            # value is just a string
            return iter([value])


class FileIterStringParamType(click.File):
    """A Click parameter type for files and strings with optional type conversion.

    Similar to FileUrlIterStringParamType but adds type conversion capability and
    doesn't handle URLs. Useful when the input needs to be parsed as a specific type.

    Args:
        type: Optional function to convert each element of the iterator

    Example:
        >>> @click.command()
        >>> @click.argument('nums', type=FileIterStringParamType('r', type=int))
        >>> def cmd(nums):
        ...     print(sum(nums))
        >>> # Valid inputs:
        >>> # numbers.txt (containing numbers)
        >>> # "42"
    """

    def __init__(self, *args, **kwargs):
        self.type = kwargs.get("type")
        if "type" in kwargs:
            del kwargs["type"]
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        """Convert the input value to an iterator with optional type conversion.

        Args:
            value: The command-line value to convert
            param: The parameter being processed
            ctx: The Click context

        Returns:
            An iterator over the input source, with optional type conversion

        Raises:
            click.BadParameter: If type conversion fails or file can't be opened
        """
        if "r" not in self.mode:
            self.fail("stream cannot be opened in non-read mode", param, ctx)

        output_iterator = None
        if exists(value):
            # value is a valid filename
            f = super().convert(value, param, ctx)
            output_iterator = iter(f)
        elif value == "-":
            # value is stdin
            output_iterator = click.get_text_stream("stdin")
        else:
            # value is just a string
            output_iterator = iter([value])
        try:
            return TypeConvertingIterator(output_iterator, self.type) if self.type else output_iterator
        except Exception as e:
            self.fail("Error while converting iterator: %s" % e, param, ctx)


class FileOrUrlParamType(click.File):
    """A Click parameter type that handles both local files and URLs.

    This parameter type extends Click's File type to also handle URLs by downloading
    their content to a temporary file.

    Example:
        >>> @click.command()
        >>> @click.argument('input', type=FileOrUrlParamType('r'))
        >>> def cmd(input):
        ...     content = input.read()
        >>> # Valid inputs:
        >>> # file.txt
        >>> # http://example.com/data
    """

    def convert(self, value, param, ctx):
        """Convert the input value to a file object.

        For URLs, downloads the content to a temporary file before returning
        a file object pointing to it.

        Args:
            value: The command-line value to convert
            param: The parameter being processed
            ctx: The Click context

        Returns:
            A file object

        Raises:
            click.BadParameter: If URL fetch fails or file can't be opened
        """
        if validators.url(value):
            # value is a url
            if "r" not in self.mode:
                self.fail("Url %s cannot be opened in non-read mode" % value, param, ctx)

            try:
                r = requests.get(value)
                if not r.ok:
                    self.fail("Url %s does not return 200 OK" % value, param, ctx)
            except Exception as e:
                self.fail("Error while fetching %s: %s" % (value, e), param, ctx)

            # Create a temporary file that will be automatically cleaned up
            with tempfile.NamedTemporaryFile(mode="wb+", delete=False) as tmpfile:
                if isinstance(r.content, str):
                    tmpfile.write(r.content.encode('utf-8'))
                else:
                    tmpfile.write(r.content)
                tmpfile.flush()
                value = tmpfile.name

                # Register cleanup with Click's context
                if ctx is not None:
                    def cleanup():
                        try:
                            import os
                            os.unlink(tmpfile.name)
                        except OSError:
                            pass
                    ctx.call_on_close(cleanup)

        return super().convert(value, param, ctx)


class StringOrFileParamType(click.File):
    """A Click parameter type that handles both direct strings and file paths.

    This parameter type allows flexibility in input, treating the value as a file path
    if it exists, otherwise treating it as a direct string by writing it to a temporary file.

    Example:
        >>> @click.command()
        >>> @click.argument('input', type=StringOrFileParamType('r'))
        >>> def cmd(input):
        ...     content = input.read()
        >>> # Valid inputs:
        >>> # file.txt
        >>> # "direct content"
    """

    def convert(self, value, param, ctx):
        """Convert the input value to a file object.

        If the value is not a valid file path, creates a temporary file containing
        the value as its content.

        Args:
            value: The command-line value to convert
            param: The parameter being processed
            ctx: The Click context

        Returns:
            A file object
        """
        if value != "-" and not exists(value):
            # Create a temporary file that will be automatically cleaned up
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
                tmpfile.write(value)
                tmpfile.flush()
                value = tmpfile.name

                # Register cleanup with Click's context
                if ctx is not None:
                    def cleanup():
                        try:
                            import os
                            os.unlink(tmpfile.name)
                        except OSError:
                            pass
                    ctx.call_on_close(cleanup)

        return super().convert(value, param, ctx)


class UrlOrListFromFileStdinParamType(click.File):
    """A Click parameter type that handles URLs or lists from files/stdin.

    This parameter type provides three input methods:
    1. A single URL (returned as a single-item list)
    2. A file containing URLs (one per line)
    3. Standard input containing URLs (one per line)

    Example:
        >>> @click.command()
        >>> @click.argument('urls', type=UrlOrListFromFileStdinParamType('r'))
        >>> def cmd(urls):
        ...     for url in urls:
        ...         print(url)
        >>> # Valid inputs:
        >>> # http://example.com
        >>> # urls.txt (containing URLs)
        >>> # - (URLs from stdin)
    """

    def convert(self, value, param, ctx):
        """Convert the input value to a list of URLs or a file object.

        Args:
            value: The command-line value to convert
            param: The parameter being processed
            ctx: The Click context

        Returns:
            Either a single-item list containing a URL or a file object
        """
        if validators.url(value):
            # value is a url
            return [value]

        return super().convert(value, param, ctx)
