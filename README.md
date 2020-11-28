# pyduration

![Tests](https://github.com/diatche/pyduration/workflows/Tests/badge.svg)

A calendar unit length utility library for Python.

# Installation

With [poetry](https://python-poetry.org):

```bash
poetry add pyduration
```

Or with pip:

```
pip3 install pyduration
```

# Usage

Have a look at the [documentation](https://diatche.github.io/pyduration/).

Basic usage:

```python
from pyduration import Duration

days = Duration('1d')
for day in days.iterate(['2020-01-01', '2020-01-31']):
    print(f'{day[0]} - {day[1]}')
```

# Development

## Updating Documentation

The module [pdoc3](https://pdoc3.github.io/pdoc/) is used to automatically generate documentation. To update the documentation:

1. Install `pdoc3` if needed with `pip3 install pdoc3`.
2. Navigate to project root and install dependencies: `poetry install`.
3. Generate documetation files with: `pdoc3 -o docs --html pyduration`.
4. The new files will be in `docs/pyduration`. Move them to `docs/` and replace existing files.
