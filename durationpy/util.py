"""
Utilities used by durationpy.
"""

import arrow
from collections.abc import Iterable, Mapping
from intervalpy import Interval
import math
from numbers import Number
from typing import Any


def filter_any(cb, a):
    if cb is None:
        cb = bool
    assert callable(cb)
    if isinstance(a, Mapping):
        return {k: v for k, v in a.items() if cb(v)}
    else:
        return list(filter(cb, a))


def flatten(items) -> list:
    return list(_flatten(items))


def _flatten(items):
    if items is None or isinstance(items, (str, bytes, Mapping)) or not isinstance(items, Iterable):
        yield items
        return
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in _flatten(x):
                yield sub_x
        else:
            yield x


def timespan(t1, t2, open=None, start_open=None, end_open=None):
    t1 = timestamp(t1)
    t2 = timestamp(t2)
    if open is not None:
        start_open = bool(open)
        end_open = bool(open)
    elif start_open is not None:
        start_open = bool(start_open)
        end_open = not bool(start_open)
    elif end_open is not None:
        start_open = not bool(end_open)
        end_open = bool(end_open)
    return Interval(t1, t2, start_open=start_open, end_open=end_open)


def timestamp(x: Any) -> float:
    if x is None:
        raise ValueError(f'Cannot parse timestamp: {x}')
    if isinstance(x, Number):
        if math.isinf(x) or math.isnan(x):
            raise ValueError(f'Cannot parse timestamp: {x}')
        return x
    return arrow.get(x).float_timestamp
