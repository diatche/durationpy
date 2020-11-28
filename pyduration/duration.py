"""
A calendar unit length utility library.

Start by importing `Duration`:

```
from pyduration import Duration
```

See Duration.
"""

import arrow
import math
import re
import warnings
import typing
from calendar import Calendar
from time import time
from typing import *
from . import util
from intervalpy import Interval
from numbers import Number
from datetime import date, timedelta
from collections.abc import Iterable, Sequence, Mapping

YEARS = 'years'
MONTHS = 'months'
WEEKS = 'weeks'
DAYS = 'days'
HOURS = 'hours'
MINUTES = 'minutes'
SECONDS = 'seconds'
MICROSECONDS = 'microseconds'


TIME_UNIT_MAP = {
    'y': YEARS,
    'M': MONTHS,
    'w': WEEKS,
    'd': DAYS,
    'h': HOURS,
    'm': MINUTES,
    's': SECONDS,
    'S': MICROSECONDS,
    'μs': MICROSECONDS
}

TIME_SYMBOL_MAP = {u: s for s, u in TIME_UNIT_MAP.items()}
TIME_SYMBOLS = set(TIME_UNIT_MAP.keys())
TIME_UNITS = set(TIME_UNIT_MAP.values())

TIME_UNITS_PLURAL = TIME_UNITS
SINGLUAR_UNIT_MAP = {u: u[:-1] for u in TIME_UNITS_PLURAL}
TIME_UNITS_SINGLUAR = set(TIME_UNIT_MAP.values())
TIME_UNITS_P_AND_S = TIME_UNITS_PLURAL.union(TIME_UNITS_SINGLUAR)

CHILDREN = {
    YEARS: [
        MONTHS,
        WEEKS,
        DAYS
    ],
    DAYS: [
        HOURS,
        MINUTES,
        SECONDS
    ],
    SECONDS: [
        MICROSECONDS
    ]
}
PARENTS: Dict[str, str] = {}
for parent, children in CHILDREN.items():
    for child in children:
        PARENTS[child] = parent

CALENDAR_UNITS = [
    YEARS,
    MONTHS,
    WEEKS
]

SECONDS_RANGES = {
    YEARS: (365 * 86400.0, 366 * 86400.0),
    MONTHS: (28 * 86400.0, 31 * 86400.0),
    WEEKS: (7 * 86400.0, 7 * 86400.0),
    DAYS: (86400.0, 86400.0),
    HOURS: (3600.0, 3600.0),
    MINUTES: (60.0, 60.0),
    SECONDS: (1.0, 1.0),
    MICROSECONDS: (1e-6, 1e-6)
}

SECONDS_AVE = {
    YEARS: 365.25 * 86400.0,
    MONTHS: 30.436875 * 86400.0,
    WEEKS: 7 * 86400.0,
    DAYS: 86400.0,
    HOURS: 3600.0,
    MINUTES: 60.0,
    SECONDS: 1.0,
    MICROSECONDS: 1e-6
}

_str_parse_cache: Dict[str, 'Duration'] = {}

# TIME_SPAN_REGEX = r'\s*(?<quantity>\d+)\s*(?<unit>((d(ays?)?)|(h((ours?)|(rs?))?)|(m((inutes?)|(ins?))?)|(s((econds?)|(ecs?))?)|\Z))+'


class Duration:
    """
    Specifies a length of time in calendar unit.
    For example, 1 day, 2 hours, 2 months, 1 week.
    """

    class units:
        year = YEARS
        month = MONTHS
        week = WEEKS
        day = DAYS
        hour = HOURS
        minute = MINUTES
        second = SECONDS
        microsecond = MICROSECONDS
        all = TIME_UNITS

    def __init__(self, *args, **kwargs):
        self._data: Dict[str, int] = {}
        self._parent = None
        self._min_seconds = None
        self.calendar = Calendar()
        data = type(self).normalized_dict(*args, **kwargs)
        self.set_descriptor(data)

    def __repr__(self):
        try:
            return self.to_str()
        except Exception as e:
            return super().__repr__() + f'({e})'

    def __eq__(self, other):
        return self.equals(other)

    def __hash__(self):
        return hash(','.join([f'{k}:{v}' for k, v in self._data.items()]))

    def equals(self, other):
        return type(self) == type(other) and \
            self._data == other._data

    @classmethod
    def parse(cls, *args, **kwargs):
        cached = cls._get_cache(*args, **kwargs)
        if cached is not None:
            return cached

        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], Duration):
            return args[0]
        else:
            r = Duration(*args, **kwargs)
            cls._set_cache(r, *args, **kwargs)
            return r

    @classmethod
    def parse_many(cls, a):
        return [cls.parse(x) for x in a]

    @property
    def degree(self):
        return list(self._data.values())[0]

    @property
    def symbol(self):
        return type(self).unit_symbol(self.unit)

    @property
    def unit(self):
        return list(self._data.keys())[0]

    @property
    def is_calendar_required(self):
        if self.unit in CALENDAR_UNITS:
            return True
        # If we are not uniformly spread out
        # in a parent interval which, requires
        # a calendar, then we also require a
        # calendar to be able to find the
        # correct strating date.
        return self.parent is not None and \
            self.parent.is_calendar_required and \
            not self.is_uniform

    @property
    def is_uniform(self):
        if self._is_uniform_special_case():
            return True
        if self.min_seconds != self.max_seconds:
            return False
        if self.parent is None:
            return True
        coef = self._seconds_coef()
        s = self.ave_seconds * coef
        min_s = self.parent.min_seconds * coef
        max_s = self.parent.max_seconds * coef
        return min_s % s == 0 and max_s % s == 0

    @property
    def parent(self):
        """
        Returns the parent calendar length, which clamps
        this calendar length's intervals its intervals.
        """
        if self._parent is None:
            if self.unit not in PARENTS:
                return None
            parent_unit = PARENTS[self.unit]
            self._parent = Duration({parent_unit: 1})
        return self._parent

    @property
    def total_seconds(self):
        if not self.is_uniform:
            raise Exception(f'Cannot convert calendar length {self} to uniform seconds')
        return self.min_seconds

    @property
    def ave_seconds(self):
        return self.degree * SECONDS_AVE[self.unit]

    @property
    def min_seconds(self):
        if self._min_seconds is None:
            s = self.degree * SECONDS_RANGES[self.unit][0]
            if self.parent is None or self.degree == 1 or self._is_uniform_special_case():
                return s
            # The last interval may be smaller
            coef = self._seconds_coef()
            s *= coef
            parent_s = self.parent.min_seconds * coef
            last_s = parent_s % s
            if last_s == 0:
                # Uniform interval
                last_s = s
            self._min_seconds = last_s / coef
        return self._min_seconds

    @property
    def max_seconds(self):
        return self.degree * SECONDS_RANGES[self.unit][1]

    def to_str(self):
        return f'{self.degree}{self.symbol}'

    def set_descriptor(self, data):
        ndata = type(self).normalized_dict(data)
        if ndata is None:
            raise Exception(f'Invalid calendar length data: {data}')
        self._data = ndata

    def get_descriptor(self):
        return dict(self._data)

    def aggregate(self, degree: int) -> 'Duration':
        """
        Returns a calendar length multiplied by the specified `degree`.
        """
        return self.with_degree(self.degree * degree)

    def with_degree(self, degree: int) -> 'Duration':
        """
        Returns a calendar length with specified `degree`.
        """
        assert degree > 0
        if degree == self.degree:
            return self
        d = self.get_descriptor()
        d = {k: degree for k, v in d.items()}
        return Duration(d)

    def iterate(self, interval, size=1, backward=False, start_open=False) -> Iterator[Optional[Interval]]:
        """
        Iterates time-spans inside a interval.
        Does not trim timespans inside the interval.
        """
        interval = Interval.parse(interval, default_inf=True)
        if interval.is_empty:
            return iter([])
        start = interval.start if not backward else interval.end
        if math.isinf(start):
            raise ValueError('Cannot iterate intervals from infinity')
        if size < 1:
            raise ValueError('Size must ba a positive integer')

        if self.is_uniform:
            interval_span = self.span_interval(interval, start_open=start_open)
            start = interval_span.start if not backward else interval_span.end
            count = math.ceil(self.count(interval_span, start_open=start_open) / size)
            step = size * self.ave_seconds
            if backward:
                step = -step
            i = 0

            def next_uniform_span():
                nonlocal start, step, i, count

                if i == count:
                    return None
                a = start + i * step
                b = a + step
                i += 1
                return Interval(min(a, b), max(a, b), start_open=start_open, end_open=not start_open)

            return iter(next_uniform_span, None)

        walker = self.walk(start, size=size, backward=backward, start_open=start_open)

        def next_span_in_interval():
            nonlocal start

            while True:
                span = next(walker)
                if span is None or span.is_empty:
                    return None
                elif span.intersects(interval):
                    return span
                elif span.contains(start):
                    # Keep looking for interval
                    continue
                else:
                    # Went outside interval
                    return None

            return None

        return iter(next_span_in_interval, None)

    def walk(
        self,
        start,
        limit: Optional[Number] = None,
        size=1,
        backward=False,
        start_open=False
    ) -> Iterator[Optional[Interval]]:
        """
        Iterates time-spans.
        """
        if limit is not None:
            if limit == 0:
                return iter([])
            if limit < 0:
                limit = -limit
                backward = not backward
        span = self.span_date(start, start_open=start_open)
        if backward:
            x1 = span.end
        else:
            x1 = span.start
        count = 0

        def next_span():
            nonlocal x1, count
            if limit is not None and count >= limit:
                return None
            count += 1
            x0 = x1
            x1 = self.step(x0, count=size, backward=backward)
            span = Interval(min(x0, x1), max(x0, x1), start_open=start_open, end_open=not start_open)
            return span

        return iter(next_span, None)

    def round(self, date) -> float:
        """
        Returns the closest boundary to the specified `date`.
        """
        ceil = self.ceil(date)
        floor = self.floor(date)
        if ceil - date <= date - floor:
            return ceil
        else:
            return floor

    def floor(self, date) -> float:
        """
        Returns the boundary at or before the specified `date`.
        """
        return self.span_date(date, start_open=False).start

    def ceil(self, date) -> float:
        """
        Returns the boundary at or after the specified `date`.
        """
        return self.span_date(date, start_open=True).end

    def next(self, date) -> float:
        """
        Returns the next boundary after the specified `date`.
        """
        return self.span_date(date, start_open=False).end

    def previous(self, date) -> float:
        """
        Returns the previous boundary before the specified `date`.
        """
        return self.span_date(date, start_open=True).start

    def step(self, date, count=1, backward=False) -> float:
        """
        Returns the `count`th boundary after or before the specified `date`.
        """
        date = self._normalized_date(date)
        if count == 0:
            return date
        if count < 0:
            backward = not backward
            count = -count
        count = int(count)
        rounder = self.ceil if not backward else self.floor
        ndate = rounder(date)
        if ndate != date:
            count -= 1

        if count > 1 and self.is_uniform:
            # Use seconds
            if backward:
                count = -count
            seconds = self.ave_seconds
            return ndate + seconds * count
        else:
            # Iterate
            step = self.next if not backward else self.previous
            for _ in range(count):
                ndate = step(ndate)
            return ndate

    def pad(self, interval, start=0, end=0, start_open=False) -> Interval:
        """
        Appends calendar lengths to the start and end of a interval.
        """
        interval = self.span_interval(interval, start_open=start_open)
        if interval.is_empty:
            return Interval.empty()

        l = interval.start
        if not interval.is_negative_infinite:
            l = self.step(l, count=start, backward=True)

        h = interval.end
        if not interval.is_positive_infinite:
            h = self.step(h, count=end)

        return Interval(l, h, start_open=start_open, end_open=not start_open)

    def span(self, x, start_open=False) -> Interval:
        """
        Returns the time interval which contains the specified single date or interval.
        """
        if isinstance(x, Number):
            return self.span_date(x, start_open=start_open)
        else:
            return self.span_interval(x, start_open=start_open)

    def span_date(self, date, start_open=False) -> Interval:
        """
        Returns the time interval which contains the specified `date`.
        """
        if self.is_calendar_required:
            return self._calendar_span(date, start_open=start_open)
        else:
            return self._non_calendar_span(date, start_open=start_open)

    def _non_calendar_span(self, date, start_open=False) -> Interval:
        # We can use seconds
        coef = self._seconds_coef()
        t = self._normalized_date(date) * coef

        if self.degree == 1:
            # Do not limit to parent for speed
            parent_start = 0
            parent_secs = math.inf
        else:
            # Start from parent start
            parent_span = self.parent.span_date(date, start_open=start_open)
            parent_start = parent_span.start * coef
            parent_secs = parent_span.length * coef

        seconds = self.ave_seconds * coef
        parent_t = t - parent_start
        start = math.floor(parent_t / seconds) * seconds
        end = math.ceil(parent_t / seconds) * seconds

        if start == end:
            if start_open:
                start -= seconds
            else:
                end += seconds

        # Limit to parent end
        if end > parent_secs:
            end = parent_secs

        start_date = parent_start + start
        end_date = parent_start + end

        start_date /= coef
        end_date /= coef

        return Interval(
            start_date,
            end_date,
            start_open=start_open,
            end_open=not start_open
        )

    def _calendar_span(self, date, start_open=False) -> Interval:
        """
        Returns the time interval which contains the specified `date`.
        """
        date = arrow.get(date)
        t = self._normalized_date(date)
        msec = timedelta(microseconds=1)
        start = date - msec
        end = date + msec
        degree = self.degree
        unit = self.unit
        sunit = type(self).singular_unit(unit)
        date_span = None

        force_agr = unit == WEEKS
        if force_agr:
            # Special case
            sunit = type(self).singular_unit(DAYS)

        # Find matching unit interval (1d, 1h, etc)
        for r0, r1 in arrow.Arrow.span_range(sunit, start, end):
            # Normalize range end
            r1 += msec
            interval = Interval(r0.float_timestamp, r1.float_timestamp, start_open=start_open, end_open=not start_open)
            if interval.contains(t):
                if degree == 1 and not force_agr:
                    return interval
                else:
                    date_span = r0, r1
                    break

        # Expand into aggregate interval
        if self.unit == YEARS:
            start_date, end_date = self._expand_years(date_span)
        elif self.parent is not None and self.parent.unit == YEARS:
            start_date, end_date = self._expand_within_year(date_span)
        else:
            raise Exception(f'Unable to expand unit: {self.unit}')

        return Interval(
            self._normalized_date(start_date),
            self._normalized_date(end_date),
            start_open=start_open,
            end_open=not start_open
        )

    def _expand_years(self, date_span):
        start_date = date_span[0]
        end_date = date_span[1]

        start_date = start_date.floor('year')
        end_date = start_date.shift(years=self.degree)

        assert end_date > start_date
        return start_date, end_date

    def _expand_within_year(self, date_span):
        start_date = date_span[0]
        end_date = date_span[1]
        degree = self.degree
        unit = self.unit

        if unit == WEEKS:
            # Limit to the 1st day of the first week
            year_start = self.calendar.monthdatescalendar(start_date.year, 1)[0][0]
            year_end = self.calendar.monthdatescalendar(start_date.year + 1, 1)[0][0]
            year_start = arrow.get(year_start)
            year_end = arrow.get(year_end)
        else:
            # Limit to the 1st January
            year_start = start_date.floor('year')
            year_end = start_date.ceil('year') + timedelta(microseconds=1)

        if end_date > year_end:
            end_date = year_end

        if unit == DAYS or unit == WEEKS:
            day_res = degree
            if unit == WEEKS:
                day_res *= 7
            
            start = (start_date - year_start).days
            start = math.floor(start / day_res) * day_res
            start_date = year_start + timedelta(days=start)

            end = (end_date - year_start).days
            end = math.ceil(end / day_res) * day_res
            end_date = year_start + timedelta(days=end)
        elif unit == MONTHS:
            start = start_date.month - 1
            start = math.floor(start / degree) * degree
            start_date = arrow.get(start_date.year, start + 1, 1)

            end = end_date.month - 1
            end = math.ceil(end / degree) * degree
            end_date = arrow.get(end_date.year, end + 1, 1)
        else:
            raise Exception(f'Unit not supported: {unit}')

        if end_date > year_end:
            end_date = year_end

        assert end_date > start_date
        return start_date, end_date

    def span_interval(self, interval, start_open=False) -> Interval:
        """
        Returns the time interval which fully contains the specified interval.
        """
        interval = Interval.parse(interval, default_inf=True)
        if interval.is_empty:
            return Interval.empty()
        elif interval.start == interval.end:
            return self.span_date(interval.start, start_open=start_open)

        end_open = not start_open

        if interval.is_negative_infinite:
            start = -math.inf
        else:
            # Move outward if interval is closed but should be open
            o = not interval.start_open and start_open
            span = self.span_date(interval.start, start_open=o)
            start = span.start

        if interval.is_positive_infinite:
            end = math.inf
        else:
            # Move outward if interval is closed but should be open
            o = not interval.end_open and end_open
            span = self.span_date(interval.end, start_open=not o)
            end = span.end

        return Interval(start, end, start_open=start_open, end_open=not start_open)

    def count(self, interval, start_open=False) -> int:
        """
        Returns the number of intervals in the specified interval.
        """
        interval = Interval.parse(interval, default_inf=True)
        if interval.is_empty:
            return 0
        if not interval.is_finite:
            raise Exception('Cannot count intervals on infinite interval')
        interval = self.span_interval(interval, start_open=start_open)

        if not self.is_uniform:
            # Walk spans
            # TODO: this can be optimised to avoid walking
            count = 0
            for _ in self.iterate(interval):
                count += 1
            return count
        else:
            # Use seconds
            return int(math.ceil(interval.length / self.ave_seconds))

    def _is_uniform_special_case(self):
        if self.unit == WEEKS and self.degree == 1:
            return True
        return False

    def _seconds_coef(self):
        """
        Apply this coefficient when comparing seconds
        to minimise floating point errors.
        """
        s = self.ave_seconds
        assert s > 0
        if s >= 1:
            return 1
        return 10 ** -round(math.log(s, 10))

    def _normalized_date(self, date):
        return util.timestamp(date)

    @classmethod
    def normalized_dict(cls, *args, **kwargs) -> Optional[Dict[str, int]]:
        args = util.flatten(args)
        split_args: List[Any] = []
        for arg in args:
            if isinstance(arg, str):
                split_args += arg.split(' ')
            else:
                split_args.append(arg)
        split_args.append(dict(kwargs))
        split_args = list(filter(None, split_args))
        args = split_args

        if len(args) == 1 and isinstance(args[0], Number):
            # Single number argument is assumed to be in seconds.
            seconds = args[0]
            if seconds < 0:
                return None
            args[0] = timedelta(seconds=seconds)

        t: Dict[str, int] = {}

        for i in range(len(args)):
            arg = args[i]
            is_str = isinstance(arg, (str, bytes))
            if isinstance(arg, Duration):
                arg = arg.get_descriptor()

            if isinstance(arg, timedelta):
                # Normalize the time components as
                # much as possible.
                date = arrow.get(arg.seconds, tzinfo='utc')
                arg = {
                    DAYS: arg.days,
                    HOURS: date.hour,
                    MINUTES: date.minute,
                    SECONDS: date.second,
                    MICROSECONDS: arg.microseconds
                }

            if is_str:
                values = re.findall(r'\d+', arg)
                units = re.findall(r'\D+', arg)
                if len(values) > 1:
                    return None
                elif len(units) > 1:
                    return None
                if len(values) == 1 and len(units) == 1:
                    arg = [values[0], units[0]]
                    is_str = False

            if is_str or not isinstance(arg, Iterable):
                if i == 0:
                    continue
                arg = [args[i - 1], args[i]]
                is_str = False

            if not is_str and isinstance(arg, Sequence):
                try:
                    val = float(arg[0])
                    unit = str(arg[1])
                    arg = {unit: val}
                except Exception:
                    continue

            if isinstance(arg, Mapping):
                for maybe_unit in arg:
                    unit = cls.parse_unit(maybe_unit)
                    if unit is None:
                        # Invalid unit
                        return None
                    if unit in t:
                        # Repeated values for one unit is dissalowed
                        return None
                    val = arg[maybe_unit]
                    if not isinstance(val, Number) or val < 0:
                        # Only positive values supported
                        return None
                    t[unit] = int(val)

        t = util.filter_any(None, t)

        if len(t) != 1:
            # A calendar length can be only be made up of one component
            return None

        return t

    @classmethod
    def parse_unit(cls, maybe_unit):
        unit = None
        if maybe_unit in TIME_SYMBOLS:
            unit = TIME_UNIT_MAP[maybe_unit]
        else:
            maybe_unit = maybe_unit.lower()
            for valid_unit in TIME_UNITS_P_AND_S:
                if valid_unit.startswith(maybe_unit):
                    unit = valid_unit
                    break
            if unit not in TIME_UNITS:
                # Invalid unit
                unit = None
        return unit

    @classmethod
    def unit_symbol(cls, unit):
        assert unit in TIME_UNITS
        return TIME_SYMBOL_MAP[unit]

    @classmethod
    def singular_unit(cls, unit):
        assert unit in TIME_UNITS
        return SINGLUAR_UNIT_MAP[unit]

    @classmethod
    def plural_unit(cls, unit):
        assert unit in TIME_UNITS
        return unit

    @classmethod
    def _seconds_arithmetic(cls, a):
        # Check for numbers
        for x in a:
            if isinstance(x, Number):
                return True

    @classmethod
    def _to_seconds(cls, a):
        seconds: List[float] = []
        for x in a:
            if isinstance(x, Duration):
                seconds.append(x.total_seconds)
                warnings.warn('Implicitly converting calendar length into seconds', UserWarning)
            else:
                seconds.append(float(x))
        return seconds

    @classmethod
    def _get_cache(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and type(args[0]) == str:
            if args[0] in _str_parse_cache:
                return _str_parse_cache[args[0]]
        return None

    @classmethod
    def _set_cache(cls, r, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and type(args[0]) == str:
            _str_parse_cache[args[0]] = r

    def __add__(self, other):
        secs = type(self)._to_seconds([self, other])
        return secs[0] + secs[1]

    def __sub__(self, other):
        secs = type(self)._to_seconds([self, other])
        return secs[0] - secs[1]

    def __mul__(self, other):
        secs = type(self)._to_seconds([self, other])
        return secs[0] * secs[1]

    def __truediv__(self, other):
        secs = type(self)._to_seconds([self, other])
        return secs[0] / secs[1]

    def __floordiv__(self, other):
        secs = type(self)._to_seconds([self, other])
        return secs[0] // secs[1]

    def __radd__(self, other):
        secs = type(self)._to_seconds([other, self])
        return secs[0] + secs[1]

    def __rsub__(self, other):
        secs = type(self)._to_seconds([other, self])
        return secs[0] - secs[1]

    def __rmul__(self, other):
        secs = type(self)._to_seconds([other, self])
        return secs[0] * secs[1]

    def __rtruediv__(self, other):
        secs = type(self)._to_seconds([other, self])
        return secs[0] / secs[1]

    def __rfloordiv__(self, other):
        secs = type(self)._to_seconds([other, self])
        return secs[0] // secs[1]

    def __neg__(self):
        return -self.total_seconds

    def __pos__(self):
        return self.total_seconds

    def __abs__(self):
        return self.total_seconds

    def __lt__(self, other):
        if isinstance(other, Number):
            return self.max_seconds < other

        if type(self) != type(other):
            raise Exception(f'Unable to compare with: {other}')
        if self.unit == other.unit:
            return self.degree < other.degree
        else:
            return self.max_seconds < other.min_seconds

    def __gt__(self, other):
        if isinstance(other, Number):
            return self.min_seconds > other

        if type(self) != type(other):
            raise Exception(f'Unable to compare with: {other}')
        if self.unit == other.unit:
            return self.degree > other.degree
        else:
            return self.min_seconds > other.max_seconds
