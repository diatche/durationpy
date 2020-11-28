# durationpy

![Tests](https://github.com/diatche/durationpy/workflows/Tests/badge.svg)

A calendar unit length utility library for Python.

# Installation

With [poetry](https://python-poetry.org):

```bash
poetry add durationpy
```

Or with pip:

```
pip3 install durationpy
```

# Usage

Have a look at the [documentation](https://diatche.github.io/durationpy/).

Basic usage:

```python
from durationpy import Duration

days = Duration('1d')
for day in days.iterate(['2020-01-01', '2020-01-31']):
    print(f'{day[0]} - {day[1]}')
```
