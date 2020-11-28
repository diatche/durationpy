from datetime import timedelta
from intervalpy import Interval
import os
import pytest
import sys
from pyduration import Duration, util

module_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir, '..', 'pyduration'))

t_ = util.timestamp


def span(t1, t2, start_open=False):
    return Interval(t_(t1), t_(t2), start_open=start_open, end_open=not start_open)


def test_init():
    assert str(Duration(1)) == '1s'
    assert str(Duration(23)) == '23s'
    assert str(Duration(60)) == '1m'
    assert str(Duration(86400)) == '1d'
    assert str(Duration('1m')) == '1m'
    assert str(Duration('1 m')) == '1m'
    assert str(Duration(1, 'm')) == '1m'
    assert str(Duration(1, 'min')) == '1m'
    assert str(Duration([2, 'min'])) == '2m'
    assert str(Duration((3, 'min'))) == '3m'
    assert str(Duration({'min': 4})) == '4m'
    assert str(Duration(min=5)) == '5m'
    assert str(Duration('1d')) == '1d'
    assert str(Duration('3d')) == '3d'
    assert str(Duration('7d')) == '7d'
    assert str(Duration('8d')) == '8d'
    assert str(Duration('1 week')) == '1w'
    assert str(Duration('1M')) == '1M'
    assert str(Duration('2 months')) == '2M'
    assert str(Duration('1y')) == '1y'
    assert str(Duration('1Y')) == '1y'
    assert str(Duration('2 years')) == '2y'
    assert str(Duration(timedelta(seconds=3))) == '3s'
    assert str(Duration(timedelta(days=7))) == '7d'
    assert str(Duration(0.123)) == '123000μs'
    assert str(Duration(0.000123)) == '123μs'
    assert str(Duration('2μs')) == '2μs'
    assert str(Duration(timedelta(microseconds=3))) == '3μs'
    assert str(Duration(Duration(60))) == '1m'
    with pytest.raises(Exception):
        _ = Duration('1')
    with pytest.raises(Exception):
        _ = Duration('1d 1h')
    with pytest.raises(Exception):
        _ = Duration(1, 2, 'h')
    with pytest.raises(Exception):
        _ = Duration('-1d')
    with pytest.raises(Exception):
        _ = Duration(-2, 'd')
    with pytest.raises(Exception):
        _ = Duration(timedelta(seconds=-3))
    with pytest.raises(Exception):
        _ = Duration()
    with pytest.raises(Exception):
        _ = Duration(0)
    with pytest.raises(Exception):
        _ = Duration(-1)
    with pytest.raises(Exception):
        _ = Duration(None)


def test_eq():
    assert Duration('1h') == Duration('1h')
    assert Duration('1h') != Duration('2h')
    assert Duration('1h') != Duration('1d')


def test_with_degree():
    assert Duration('1h').with_degree(4) == Duration('4h')


def test_parent():
    assert Duration('1S').parent == Duration('1s')
    assert Duration('1s').parent == Duration('1d')
    assert Duration('1m').parent == Duration('1d')
    assert Duration('1h').parent == Duration('1d')
    assert Duration('1m').parent == Duration('1d')

    assert Duration('1d').parent == Duration('1y')
    assert Duration('1w').parent == Duration('1y')
    assert Duration('1y').parent is None


def test_is_uniform():
    assert Duration('1S').is_uniform is True
    assert Duration('2S').is_uniform is True

    assert Duration('1s').is_uniform is True
    assert Duration('2s').is_uniform is True

    assert Duration('1m').is_uniform is True
    assert Duration('2m').is_uniform is True
    assert Duration('3m').is_uniform is True
    assert Duration('5m').is_uniform is True
    assert Duration('6m').is_uniform is True
    assert Duration('7m').is_uniform is False
    assert Duration('8m').is_uniform is True
    assert Duration('9m').is_uniform is True
    assert Duration('12m').is_uniform is True
    assert Duration('15m').is_uniform is True
    assert Duration('30m').is_uniform is True

    assert Duration('1h').is_uniform is True
    assert Duration('2h').is_uniform is True
    assert Duration('3h').is_uniform is True
    assert Duration('5h').is_uniform is False
    assert Duration('6h').is_uniform is True
    assert Duration('7h').is_uniform is False
    assert Duration('8h').is_uniform is True
    assert Duration('9h').is_uniform is False
    assert Duration('12h').is_uniform is True

    assert Duration('1d').is_uniform is True
    assert Duration('2d').is_uniform is False

    assert Duration('1w').is_uniform is True
    assert Duration('2w').is_uniform is False

    assert Duration('1M').is_uniform is False
    assert Duration('2M').is_uniform is False

    assert Duration('1y').is_uniform is False
    assert Duration('2y').is_uniform is False


def test_is_calendar_required():
    assert Duration('1S').is_calendar_required is False
    assert Duration('1323S').is_calendar_required is False

    assert Duration('1s').is_calendar_required is False
    assert Duration('59s').is_calendar_required is False

    assert Duration('1m').is_calendar_required is False
    assert Duration('59m').is_calendar_required is False

    assert Duration('1h').is_calendar_required is False
    assert Duration('23h').is_calendar_required is False

    assert Duration('1d').is_calendar_required is False
    assert Duration('2d').is_calendar_required is True

    assert Duration('1w').is_calendar_required is True
    assert Duration('2w').is_calendar_required is True

    assert Duration('1M').is_calendar_required is True
    assert Duration('2M').is_calendar_required is True

    assert Duration('1y').is_calendar_required is True
    assert Duration('2y').is_calendar_required is True


def test_min_seconds():
    assert Duration('1h').min_seconds == 3600
    assert Duration('23h').min_seconds == 3600


def test_max_seconds():
    assert Duration('1h').max_seconds == 3600
    assert Duration('23h').max_seconds == 23 * 3600


def test_span_date_non_calendar_uniform():
    t = t_('2018-12-07 13:12')
    assert Duration('1S').span_date(1) == span(1, 1 + 1e-6)
    assert Duration('1s').span_date(1) == span(1, 2)
    assert Duration('1s').span_date(1) == span(1, 2)
    assert Duration('1m').span_date(1) == span(0, 60)
    assert Duration('1h').span_date(1) == span(0, 3600)
    assert Duration('1h').span_date(3600, start_open=False) == span(3600, 2 * 3600, start_open=False)
    assert Duration('1h').span_date(3600, start_open=True) == span(0, 3600, start_open=True)
    assert Duration('2h').span_date(1) == span(0, 2 * 3600)
    assert Duration('4h').span_date(t) == span('2018-12-07 12:00', '2018-12-07 16:00')
    assert Duration('1d').span_date(t) == span('2018-12-07', '2018-12-08')


def test_span_date_non_calendar_non_uniform():
    assert Duration('20h').span_date('2018-12-07 13:12') == span('2018-12-07 00:00', '2018-12-07 20:00')
    assert Duration('20h').span_date('2018-12-07 20:01') == span('2018-12-07 20:00', '2018-12-08 00:00')
    assert Duration('20h').span_date('2018-12-07 20:00', start_open=False) == span('2018-12-07 20:00', '2018-12-08 00:00', start_open=False)
    assert Duration('20h').span_date('2018-12-07 20:00', start_open=True) == span('2018-12-07 00:00', '2018-12-07 20:00', start_open=True)


def test_span_date_calendar_uniform():
    t = t_('2018-12-07 13:12')
    assert Duration('1d').span_date(t) == span('2018-12-07', '2018-12-08')
    assert Duration('2d').span_date(t) == span('2018-12-07', '2018-12-09')
    assert Duration('100d').span_date(t) == span('2018-10-28', '2019-01-01')
    assert Duration('1w').span_date(t) == span('2018-12-03', '2018-12-10')
    assert Duration('2w').span_date(t) == span('2018-12-03', '2018-12-17')
    # The last day of the last week of 2018 is 30/12/2018
    assert Duration('20w').span_date(t) == span('2018-10-08', '2018-12-31')
    assert Duration('1M').span_date(t) == span('2018-12-01', '2019-01-01')
    assert Duration('2M').span_date(t) == span('2018-11-01', '2019-01-01')
    assert Duration('1y').span_date(t) == span('2018-01-01', '2019-01-01')
    assert Duration('2y').span_date(t) == span('2018-01-01', '2020-01-01')


def test_span_date_non_calendar_non_uniform():
    assert Duration('200d').span_date('2018-04-07 13:12') == span('2018-01-01', '2018-07-20')
    assert Duration('200d').span_date('2018-12-07 20:01') == span('2018-07-20', '2019-01-01')
    assert Duration('200d').span_date('2018-07-20', start_open=False) == span('2018-07-20', '2019-01-01', start_open=False)
    assert Duration('200d').span_date('2018-07-20', start_open=True) == span('2018-01-01', '2018-07-20', start_open=True)


def test_span_interval():
    assert Duration('1h').span_interval(Interval.open(3600, 2 * 3600), start_open=False) == span(3600, 2 * 3600, start_open=False)
    assert Duration('1h').span_interval(Interval.open(3600, 2 * 3600), start_open=True) == span(3600, 2 * 3600, start_open=True)
    assert Duration('1h').span_interval(Interval.closed(3600, 2 * 3600), start_open=False) == span(3600, 3 * 3600, start_open=False)
    assert Duration('1h').span_interval(Interval.closed(3600, 2 * 3600), start_open=True) == span(0, 2 * 3600, start_open=True)


def test_floor():
    assert Duration('1h').floor('2018-12-07 13:12') == t_('2018-12-07 13:00')

    assert Duration('1d').floor('2018-12-07 13:12') == t_('2018-12-07')
    assert Duration('1d').floor('2018-12-07') == t_('2018-12-07')
    assert Duration('1d').floor('2018-12-31') == t_('2018-12-31')
    assert Duration('1d').floor('2019-01-01') == t_('2019-01-01')


def test_ceil():
    assert Duration('1h').ceil('2018-12-07 13:12') == t_('2018-12-07 14:00')

    assert Duration('1d').ceil('2018-12-07 13:12') == t_('2018-12-08')
    assert Duration('1d').ceil('2018-12-07') == t_('2018-12-07')
    assert Duration('1d').ceil('2018-12-31') == t_('2018-12-31')
    assert Duration('1d').ceil('2019-01-01') == t_('2019-01-01')


def test_step_uniform():
    assert Duration('1d').step('2018-12-07 13:12', count=0) == t_('2018-12-07 13:12')
    assert Duration('1d').step('2018-12-07 13:12', count=1) == t_('2018-12-08')
    assert Duration('1d').step('2018-12-07', count=1) == t_('2018-12-08')

    assert Duration('1d').step('2018-12-07 13:12', count=0, backward=True) == t_('2018-12-07 13:12')
    assert Duration('1d').step('2018-12-07 13:12', count=1, backward=True) == t_('2018-12-07')
    assert Duration('1d').step('2018-12-07', count=1, backward=True) == t_('2018-12-06')
    
    assert Duration('1d').step('2018-12-07 13:12', count=-1) == t_('2018-12-07')
    assert Duration('1d').step('2018-12-07', count=-1) == t_('2018-12-06')

    assert Duration('1d').step('2018-12-07 13:12', count=10) == t_('2018-12-17')
    assert Duration('1d').step('2018-12-07', count=10) == t_('2018-12-17')

    assert Duration('1d').step('2018-12-07 13:12', count=-5) == t_('2018-12-03')
    assert Duration('1d').step('2018-12-07', count=-5) == t_('2018-12-02')


def test_step_non_uniform():
    assert Duration('1M').step('2018-06-07 13:12', count=0) == t_('2018-06-07 13:12')
    assert Duration('1M').step('2018-06-07 13:12', count=1) == t_('2018-07-01')
    assert Duration('1M').step('2018-06-01', count=1) == t_('2018-07-01')

    assert Duration('1M').step('2018-06-07 13:12', count=0, backward=True) == t_('2018-06-07 13:12')
    assert Duration('1M').step('2018-06-07 13:12', count=1, backward=True) == t_('2018-06-01')
    assert Duration('1M').step('2018-06-01', count=1, backward=True) == t_('2018-05-01')
    
    assert Duration('1M').step('2018-06-07 13:12', count=-1) == t_('2018-06-01')
    assert Duration('1M').step('2018-06-01', count=-1) == t_('2018-05-01')

    assert Duration('1M').step('2018-06-07 13:12', count=3) == t_('2018-09-01')
    assert Duration('1M').step('2018-06-01', count=3) == t_('2018-09-01')

    assert Duration('1M').step('2018-06-07 13:12', count=-3) == t_('2018-04-01')
    assert Duration('1M').step('2018-06-01', count=-3) == t_('2018-03-01')


def test_walk():
    spans = list(Duration('1h').walk(2 * 3600, limit=2, start_open=False))
    assert spans == [
        span(2 * 3600, 3 * 3600, start_open=False),
        span(3 * 3600, 4 * 3600, start_open=False)
    ]

    spans = list(Duration('1h').walk(2 * 3600, limit=2, start_open=True))
    assert spans == [
        span(1 * 3600, 2 * 3600, start_open=True),
        span(2 * 3600, 3 * 3600, start_open=True)
    ]

    spans = list(Duration('1h').walk(2 * 3600, limit=2, backward=True, start_open=False))
    assert spans == [
        span(2 * 3600, 3 * 3600, start_open=False),
        span(1 * 3600, 2 * 3600, start_open=False)
    ]

    spans = list(Duration('1h').walk(2 * 3600, limit=2, backward=True, start_open=True))
    assert spans == [
        span(1 * 3600, 2 * 3600, start_open=True),
        span(0 * 3600, 1 * 3600, start_open=True)
    ]

    r = Duration('1h')
    for s in r.walk(2 * 3600, limit=10):
        assert s == span(2 * 3600, 3 * 3600)
        break
    for s in r.walk(2 * 3600, limit=10):
        assert s == span(2 * 3600, 3 * 3600)
        break


def test_walk_sized():
    spans = list(Duration('1h').walk(2 * 3600, size=2, limit=2, start_open=False))
    assert spans == [
        span(2 * 3600, 4 * 3600, start_open=False),
        span(4 * 3600, 6 * 3600, start_open=False)
    ]

    spans = list(Duration('1h').walk(2 * 3600, size=2, limit=2, start_open=True))
    assert spans == [
        span(1 * 3600, 3 * 3600, start_open=True),
        span(3 * 3600, 5 * 3600, start_open=True)
    ]

    spans = list(Duration('1h').walk(2 * 3600, size=2, limit=2, backward=True, start_open=False))
    assert spans == [
        span(1 * 3600, 3 * 3600, start_open=False),
        span(-1 * 3600, 1 * 3600, start_open=False)
    ]

    spans = list(Duration('1h').walk(2 * 3600, size=2, limit=2, backward=True, start_open=True))
    assert spans == [
        span(0 * 3600, 2 * 3600, start_open=True),
        span(-2 * 3600, 0 * 3600, start_open=True)
    ]


def test_iterate_uniform():
    spans = list(Duration('1h').iterate(Interval.closed(2 * 3600, 4 * 3600), start_open=False))
    assert len(spans) == 3
    assert spans[0] == span(2 * 3600, 3 * 3600, start_open=False)
    assert spans[1] == span(3 * 3600, 4 * 3600, start_open=False)
    assert spans[2] == span(4 * 3600, 5 * 3600, start_open=False)

    spans = list(Duration('1h').iterate(Interval.closed(2 * 3600, 4 * 3600), backward=True, start_open=False))
    assert len(spans) == 3
    assert spans[0] == span(4 * 3600, 5 * 3600, start_open=False)
    assert spans[1] == span(3 * 3600, 4 * 3600, start_open=False)
    assert spans[2] == span(2 * 3600, 3 * 3600, start_open=False)


def test_iterate_non_uniform():
    spans = list(Duration('1M').iterate(
        util.timespan('2018-05-02', '2018-06-03', start_open=False),
        start_open=False
    ))
    assert len(spans) == 2
    assert spans[0] == util.timespan('2018-05-01', '2018-06-01', start_open=False)
    assert spans[1] == util.timespan('2018-06-01', '2018-07-01', start_open=False)

    spans = list(Duration('1M').iterate(
        util.timespan('2018-05-02', '2018-06-03', start_open=False),
        backward=True,
        start_open=False
    ))
    assert len(spans) == 2
    assert spans[0] == util.timespan('2018-06-01', '2018-07-01', start_open=False)
    assert spans[1] == util.timespan('2018-05-01', '2018-06-01', start_open=False)


def test_iterate_uniform_large_size():
    d = Duration('1d')
    spans = list(d.iterate(util.timespan('2018-05-01', '2018-05-10', start_open=False), size=8, start_open=False))
    assert len(spans) == 2
    assert d.count(spans[0], start_open=False) == 8
    assert d.count(spans[1], start_open=False) == 8
    assert spans[0] == util.timespan('2018-05-01', '2018-05-09', start_open=False)
    assert spans[1] == util.timespan('2018-05-09', '2018-05-17', start_open=False)

    spans = list(d.iterate(util.timespan('2018-05-20', '2018-05-30', start_open=False), size=8, backward=True, start_open=False))
    assert len(spans) == 2
    assert d.count(spans[0], start_open=False) == 8
    assert d.count(spans[1], start_open=False) == 8
    assert spans[0] == util.timespan('2018-05-22', '2018-05-30', start_open=False)
    assert spans[1] == util.timespan('2018-05-14', '2018-05-22', start_open=False)


def test_iterate_non_uniform_large_size():
    M = Duration('1M')
    spans = list(M.iterate(util.timespan('2018-05-02', '2018-08-10', start_open=False), size=2, start_open=False))
    assert len(spans) == 2
    assert M.count(spans[0], start_open=False) == 2
    assert M.count(spans[1], start_open=False) == 2
    assert spans[0] == util.timespan('2018-05-01', '2018-07-01', start_open=False)
    assert spans[1] == util.timespan('2018-07-01', '2018-09-01', start_open=False)

    spans = list(M.iterate(util.timespan('2018-05-02', '2018-08-10', start_open=False), size=2, backward=True, start_open=False))
    assert len(spans) == 2
    assert M.count(spans[0], start_open=False) == 2
    assert M.count(spans[1], start_open=False) == 2
    assert spans[0] == util.timespan('2018-07-01', '2018-09-01', start_open=False)
    assert spans[1] == util.timespan('2018-05-01', '2018-07-01', start_open=False)


def test_count():
    assert Duration('1h').count(Interval.open(2 * 3600, 4 * 3600), start_open=False) == 2


def test_pad():
    assert Duration('1d').pad(span('2018-03-10', '2019-03-20'), start=2, end=3) == span('2018-03-08', '2019-03-23')


def test_next():
    assert Duration('1h').next('2018-12-07 13:12') == t_('2018-12-07 14:00')

    assert Duration('1d').next('2018-12-07 13:12') == t_('2018-12-08')
    assert Duration('1d').next('2018-12-07') == t_('2018-12-08')
    assert Duration('1d').next('2018-12-31') == t_('2019-01-01')
    assert Duration('1d').next('2019-01-01') == t_('2019-01-02')


def test_previous():
    assert Duration('1h').previous('2018-12-07 13:12') == t_('2018-12-07 13:00')

    assert Duration('1d').previous('2018-12-07 13:12') == t_('2018-12-07')
    assert Duration('1d').previous('2018-12-07') == t_('2018-12-06')
    assert Duration('1d').previous('2018-12-31') == t_('2018-12-30')
    assert Duration('1d').previous('2019-01-01') == t_('2018-12-31')


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_implicit_arithmetic():
    assert Duration('1h') + 1 == 3601
    assert Duration('1h') - 1 == 3599
    assert Duration('1h') * 10 == 36000
    assert Duration('1h') / 10 == 360
    assert 1 + Duration('1h') == 3601
    assert 1 - Duration('1h') == -3599
    assert 10 * Duration('1h') == 36000
    assert 10 / Duration('1h') == 10 / 3600
    assert -Duration('1h') == -3600
    assert +Duration('1h') == 3600
    assert abs(Duration('1h')) == 3600

    with pytest.raises(Exception):
        _ = Duration('23h') / 10
