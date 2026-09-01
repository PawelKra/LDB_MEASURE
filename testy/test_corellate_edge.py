"""Characterisation tests for degenerate crossdating input.

These pin *current* behaviour so the P1/P2 vectorisation has a baseline; they
are not an endorsement of it.  Two rough edges are recorded on purpose:

* a constant ring series has no defined correlation - the coefficient comes
  back as nan, and the divide is guarded so no ``RuntimeWarning`` escapes
  (pytest.ini would promote one to an error);
* a sample shorter than the offset window silently yields no results.
"""
import math
import warnings

import classes


def ramp(n, start=100.0, step=1.0):
    return [start + step * k for k in range(n)]


def seq(name, data):
    return classes.Sequence({'KeyCode': name, 'DateBegin': 1,
                             'measurements': list(data)})


def test_constant_series_yields_nan_without_a_warning():
    const = seq('C', [120.0] * 80)
    other = seq('O', ramp(80))
    with warnings.catch_warnings():
        warnings.simplefilter('error')          # any RuntimeWarning -> fail
        rows = classes.corellate(const, other, count=3)
    assert rows
    # crosscoef has no defined value for a constant window -> nan, propagated
    assert math.isnan(rows[0][0])


def test_constant_series_in_corellate_position_also_yields_nan_no_warning():
    const = classes.Sequence({'KeyCode': 'C', 'DateBegin': 1000,
                              'measurements': [90.0] * 60})
    other = classes.Sequence({'KeyCode': 'O', 'DateBegin': 1000,
                              'measurements': ramp(60)})
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        res = classes.corellate_position(const, other)
    assert math.isnan(res[0])


def test_sample_shorter_than_offset_window_returns_no_rows():
    # offset loop starts at i = 25 - len(sample) and ends at len(ref) - 25
    tiny = seq('S', ramp(6))
    ref = seq('R', ramp(40))
    assert classes.corellate(tiny, ref) == []


def test_offset_window_opens_once_sample_and_ref_are_long_enough():
    sample = seq('S', [100 + 8 * math.sin(k / 3.0) for k in range(30)])
    ref = seq('R', [100 + 8 * math.sin(k / 3.0 + 0.3) for k in range(90)])
    rows = classes.corellate(sample, ref)
    assert rows                       # non-empty once past the length gate
    assert all(len(r) == 11 for r in rows)


def test_reference_shorter_than_sample_still_correlates():
    ref = seq('R', [100 + 10 * math.sin(k / 4.0) for k in range(45)])
    sample = seq('S', [100 + 10 * math.sin(k / 4.0 + 0.2) for k in range(120)])
    rows = classes.corellate(sample, ref, count=5)
    assert rows
    # overlap can never exceed the shorter series
    assert max(r[8] for r in rows) <= 45
