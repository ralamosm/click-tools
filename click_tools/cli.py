import itertools
import tempfile
from os.path import exists

import click
import requests
import validators


class TypeConvertingIterator:
    def __init__(self, iterator, conversion_function=None):
        self.iterator = iterator
        self.conversion_function = conversion_function
        self._check_convertibility()

    def __iter__(self):
        return self

    def __next__(self):
        return self.conversion_function(next(self.iterator)) if self.conversion_function is not None else next(self.iterator)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.iterator.__repr__()}, {self.type})"

    def _check_convertibility(self):
        # Create a new iterator sharing input with the original iterator
        tee_iterator, self.iterator = itertools.tee(self.iterator)
        self.conversion_function(next(tee_iterator))


class ChoiceCommaSeparated(click.ParamType):
    """
    Custom click param type that handles a comma separated value
    as a list, checking against a list of valid choices
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
    """
    Custon click param type that handles a comma separated value
    as a list
    """

    name = "list-comma-separated"

    def __init__(self, *args, **kwargs):
        self.unique = kwargs.get("unique", True)
        super().__init__(*args, **kwargs)

    def convert(self, value, *args):
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
    """
    Custom click param type that handles a string (with whatever value)
    as input or stdin as '-'
    """

    name = "strings-list-or-stdin"

    def convert(self, value, param, ctx):
        if value == "-":
            return click.get_text_stream("stdin")
        else:
            if isinstance(value, str):
                return [value]
            else:
                return value


class FileUrlIterStringParamType(click.File):
    """
    Custom click param type that handles a param as:
    - a file
    - a url
    - an interator
    - or just a string

    Returns an iterator
    """

    def convert(self, value, param, ctx):
        if "r" not in self.mode:
            self.fail("stream cannot be opened in non-read mode", param, ctx)

        if exists(value):
            # value is a valid filename
            f = super().convert(value, param, ctx)
            return iter(f)
        elif validators.url(value):
            # value is a url
            try:
                r = requests.get(value, stream=True)
            except Exception as e:
                self.fail("Error while fetching %s: %s" % (value, e), param, ctx)

            if r.ok:
                return r.iter_lines()
            else:
                self.fail("Url %s does not return 200 OK" % value, param, ctx)
        elif value == "-":
            # value is stdin
            return click.get_text_stream("stdin")
        else:
            # value is just a string
            return iter([value])


class FileIterStringParamType(click.File):
    """
    Custom click param type that handles a param as:
    - a file
    - stdin
    - a string

    Arguments:
        - type (optional): a type to cast the elements of the iterator to be returned

    Returns an iterator
    """

    def __init__(self, *args, **kwargs):
        self.type = kwargs.get("type")
        if "type" in kwargs:
            del kwargs["type"]
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
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
    """
    Custom click param type that handles URLS and
    local files as the File param type
    """

    def convert(self, value, param, ctx):
        if validators.url(value):
            # value is a url
            if "r" not in self.mode:
                self.fail("Url %s cannot be opened in non-read mode" % value, param, ctx)

            try:
                r = requests.get(value)
            except Exception as e:
                self.fail("Error while fetching %s: %s" % (value, e), param, ctx)

            tmpfile = tempfile.NamedTemporaryFile(mode="wb+")
            tmpfile.write(r.content)
            tmpfile.seek(0)

            if ctx is not None:
                ctx.call_on_close(click.utils.safecall(tmpfile.close))

            value = tmpfile.name

        return super().convert(value, param, ctx)


class StringOrFileParamType(click.File):
    """
    Custom click param type that handles a string (with whatever value)
    as input or defaults to File param
    """

    def convert(self, value, param, ctx):
        if value != "-" and not exists(value):
            # value is not a valid filename, treat as string
            tmpfile = tempfile.NamedTemporaryFile(mode="w+")
            tmpfile.write(value)
            tmpfile.seek(0)

            if ctx is not None:
                ctx.call_on_close(click.utils.safecall(tmpfile.close))

            value = tmpfile.name

        return super().convert(value, param, ctx)


class UrlOrListFromFileStdinParamType(click.File):
    """
    Custom click param type that gets a list from:
    - a url (passed as param, but not visiting it, the list is just that one url)
    - a file (each line is passed as an element of the list)
    - stdin (same as above)
    """

    def convert(self, value, param, ctx):
        if validators.url(value):
            # value is a url
            return [value]

        return super().convert(value, param, ctx)
