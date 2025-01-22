# Click Tools

A collection of useful custom parameter types and utilities for Python Click applications.

## Installation

```bash
pip install click-tools
```

## Components

### TypeConvertingIterator

A utility class that wraps an iterator and applies a conversion function to each element.

```python
from click_tools import TypeConvertingIterator

# Convert strings to integers
numbers = TypeConvertingIterator(['1', '2', '3'], int)
list(numbers)  # [1, 2, 3]
```

### ChoiceCommaSeparated

A parameter type that handles comma-separated values and validates them against a list of choices.

```python
import click
from click_tools import ChoiceCommaSeparated

@click.command()
@click.option('--fruits', type=ChoiceCommaSeparated(['apple', 'banana', 'orange']))
def process_fruits(fruits):
    print(fruits)

# Valid usage:
# $ python script.py --fruits "apple,banana"
# $ python script.py --fruits "apple,orange"
# $ python script.py --fruits "*"  # Gets all choices
```

Features:
- Supports wildcard (`*` or `all`) to select all choices
- Optional case sensitivity
- Validates each value against the provided choices

### ListCommaSeparated

A parameter type that converts comma-separated strings into a list.

```python
import click
from click_tools import ListCommaSeparated

@click.command()
@click.option('--tags', type=ListCommaSeparated())
def process_tags(tags):
    print(tags)

# Usage:
# $ python script.py --tags "tag1,tag2,tag3"
# ['tag1', 'tag2', 'tag3']
```

Features:
- Automatically removes duplicates (can be disabled)
- Strips whitespace from values

### StringsListOrStdinParamType

A parameter type that accepts either a string value or reads from stdin using '-'.

```python
import click
from click_tools import StringsListOrStdinParamType

@click.command()
@click.argument('input', type=StringsListOrStdinParamType())
def process_input(input):
    for line in input:
        print(line)

# Usage:
# $ python script.py "direct input"
# $ echo "from stdin" | python script.py -
```

### FileUrlIterStringParamType

A versatile parameter type that handles files, URLs, and direct strings, returning an iterator.

```python
import click
from click_tools import FileUrlIterStringParamType

@click.command()
@click.argument('source', type=FileUrlIterStringParamType('r'))
def process_source(source):
    for line in source:
        print(line)

# Usage:
# $ python script.py file.txt
# $ python script.py http://example.com/data
# $ python script.py "direct string"
```

Features:
- Handles local files
- Supports URLs (returns line iterator)
- Accepts stdin with '-'
- Converts direct strings to single-item iterators

### FileIterStringParamType

Similar to FileUrlIterStringParamType but focused on files and direct strings, with type conversion support.

```python
import click
from click_tools import FileIterStringParamType

@click.command()
@click.argument('numbers', type=FileIterStringParamType('r', type=int))
def sum_numbers(numbers):
    print(sum(numbers))

# Usage:
# $ python script.py numbers.txt
# $ python script.py "42"
```

### FileOrUrlParamType

A parameter type that handles both local files and URLs, downloading URL content to a temporary file.

```python
import click
from click_tools import FileOrUrlParamType

@click.command()
@click.argument('input', type=FileOrUrlParamType('r'))
def process_file(input):
    content = input.read()
    print(content)

# Usage:
# $ python script.py file.txt
# $ python script.py http://example.com/data
```

### StringOrFileParamType

A parameter type that treats the input as either a direct string or a file path.

```python
import click
from click_tools import StringOrFileParamType

@click.command()
@click.argument('content', type=StringOrFileParamType('r'))
def process_content(content):
    print(content.read())

# Usage:
# $ python script.py file.txt
# $ python script.py "direct content"
```

### UrlOrListFromFileStdinParamType

A parameter type that creates a list from a URL, file contents, or stdin.

```python
import click
from click_tools import UrlOrListFromFileStdinParamType

@click.command()
@click.argument('urls', type=UrlOrListFromFileStdinParamType('r'))
def process_urls(urls):
    for url in urls:
        print(url)

# Usage:
# $ python script.py http://example.com  # Single URL
# $ python script.py urls.txt  # File with URLs
# $ cat urls.txt | python script.py -  # URLs from stdin
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
