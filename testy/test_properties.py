"""Property-based tests (hypothesis).

The example-based suites pin known cases; these hammer the invariants with
random input to surface the edge cases nobody wrote a test for:

  * Sequence: DateEnd / Length stay consistent under every mutation
  * DataBase: add_seq keeps keys unique, get() never auto-creates
  * file I/O: write -> read is loss-free for the round-trippable formats
  * corellate: never raises, bounded coefficients, offsets in range
"""
import math

import pytest
from hypothesis import assume, given, settings, strategies as st

import classes
from dendro import io as dio

rings = st.lists(st.integers(min_value=1, max_value=9999),
                 min_size=1, max_size=200)
small_rings = st.lists(st.integers(min_value=1, max_value=5000),
                       min_size=1, max_size=120)
years = st.integers(min_value=-500, max_value=3000)


# --- Sequence invariants -------------------------------------------

@given(meas=rings, beg=years)
def test_dateend_is_always_begin_plus_length_minus_one(meas, beg):
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': beg,
                          'measurements': list(meas)})
    assert s.Length() == len(meas)
    assert s.DateEnd() == s.DateBegin() + s.Length() - 1


@given(meas=rings, beg=years, new_end=years)
def test_setdateend_moves_end_without_touching_the_rings(meas, beg, new_end):
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': beg,
                          'measurements': list(meas)})
    before = list(s.measurements())

    s.setDateEnd(new_end)

    assert s.DateEnd() == new_end
    assert s.measurements() == before
    assert s.Length() == len(before)


@given(meas=rings, beg=years, new_beg=years)
def test_setdatebegin_keeps_length(meas, beg, new_beg):
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': beg,
                          'measurements': list(meas)})
    s.setDateBegin(new_beg)
    assert s.DateBegin() == new_beg
    assert s.Length() == len(meas)


@given(meas=rings, beg=years)
def test_measure_from_year_matches_index(meas, beg):
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': beg,
                          'measurements': list(meas)})
    for i, v in enumerate(meas):
        assert s.measure_from_year(s.DateBegin() + i) == v
    assert s.measure_from_year(s.DateBegin() - 1) is False
    assert s.measure_from_year(s.DateEnd() + 1) is False


@given(meas=rings, beg=years, val=st.integers(min_value=1, max_value=9999))
def test_add_then_delete_year_measurement_is_identity(meas, beg, val):
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': beg,
                          'measurements': list(meas)})
    n0 = s.Length()
    y = s.DateBegin() + n0 // 2                 # somewhere inside the range

    s.add_year_measurement(y, val)
    assert s.Length() == n0 + 1
    assert s.measure_from_year(y) == val

    s.delete_year_measurement(y)
    assert s.Length() == n0
    assert s.measurements() == list(meas)


# --- DataBase ----------------------------------------------------

@given(names=st.lists(st.sampled_from(['A', 'B', 'C', 'D']),
                      min_size=1, max_size=12))
def test_add_seq_keeps_keycodes_unique(names):
    db = classes.DataBase('s')
    for i, n in enumerate(names):
        db.add_seq('s', {n: classes.Sequence({'KeyCode': n,
                                              'measurements': [1, 2, 3]})})
    keys = list(db['s'].keys())
    assert len(keys) == len(set(keys)) == len(names)


@given(key=st.text(min_size=1, max_size=8))
def test_get_never_auto_creates(key):
    db = classes.DataBase('s')
    assert db.get('s', key) is None
    assert db.count_seqs('s') == 0
    assert db.get('nope', key) is None


# --- file round-trips -----------------------------------------

def _seqs(draw_lists, with_dates=True):
    out = {}
    for i, m in enumerate(draw_lists):
        name = 'S%d' % i
        rec = {'KeyCode': name, 'measurements': list(m)}
        if with_dates:
            rec['DateBegin'] = 1000 + i * 7
        out[name] = classes.Sequence(rec)
    return out


@settings(deadline=None, max_examples=60)
@given(lists=st.lists(rings, min_size=1, max_size=4))
def test_fh_round_trip_preserves_rings(tmp_path_factory, lists):
    src = _seqs(lists)
    p = tmp_path_factory.mktemp('fh') / 'x.fh'
    dio.write(str(p), src)
    back = dio.read(str(p))
    assert {n: s.measurements() for n, s in back.items()} == \
           {n: s.measurements() for n, s in src.items()}


@settings(deadline=None, max_examples=60)
@given(lists=st.lists(rings, min_size=1, max_size=4))
def test_json_round_trip_preserves_rings_and_dates(tmp_path_factory, lists):
    src = _seqs(lists)
    p = tmp_path_factory.mktemp('json') / 'x.json'
    dio.write(str(p), src)
    back = dio.read(str(p))
    for n, s in src.items():
        assert back[n].measurements() == s.measurements()
        assert back[n].DateBegin() == s.DateBegin()


@settings(deadline=None, max_examples=60)
@given(lists=st.lists(rings, min_size=1, max_size=3))
def test_rwl_round_trip_preserves_rings(tmp_path_factory, lists):
    src = _seqs(lists)
    p = tmp_path_factory.mktemp('rwl') / 'x.rwl'
    dio.write(str(p), src)
    back = dio.read(str(p))
    assert {n: s.measurements() for n, s in back.items()} == \
           {n: s.measurements() for n, s in src.items()}


@settings(deadline=None, max_examples=60)
@given(m=st.lists(st.integers(min_value=1, max_value=2000),
                  min_size=1, max_size=120))
def test_avr_round_trip_preserves_rings(tmp_path_factory, m):
    # the Cracow binary format packs each ring as two signed bytes
    seq = classes.Sequence({'KeyCode': 'S', 'measurements': list(m)})
    p = tmp_path_factory.mktemp('avr') / 'S.avr'
    dio.write(str(p), {'S': seq})
    assert dio.read(str(p))['S'].measurements() == list(m)


# --- corellate ----------------------------------------------

corr_list = st.lists(st.integers(min_value=10, max_value=400),
                     min_size=30, max_size=140)


@settings(deadline=None, max_examples=80)
@given(a=corr_list, b=corr_list, count=st.integers(min_value=1, max_value=20))
def test_corellate_is_bounded_and_never_raises(a, b, count):
    # a constant series is a documented degenerate case (it warns, see
    # test_corellate_edge); real ring-width series always vary
    assume(len(set(a)) > 1 and len(set(b)) > 1)
    sa = classes.Sequence({'KeyCode': 'a', 'measurements': list(a)})
    sb = classes.Sequence({'KeyCode': 'b', 'measurements': list(b)})

    rows = classes.corellate(sa, sb, count)

    assert len(rows) <= count
    na, nb = len(a), len(b)
    for row in rows:
        cc = row[0]
        assert math.isnan(cc) or -1.0001 <= cc <= 1.0001
        assert 25 - na <= row[7] < nb - 25          # offset within lag window
        assert row[-2] == 'a' and row[-1] == 'b'


@given(x=st.lists(st.integers(min_value=1, max_value=400),
                  min_size=5, max_size=120))
def test_fast_r_of_a_series_with_itself_is_one(x):
    import numpy as np
    assume(len(set(x)) > 1)                  # a constant series -> nan, not 1
    arr = np.asarray(x, dtype=float)
    assert abs(classes._fast_r(arr, arr) - 1.0) < 1e-9


@settings(deadline=None, max_examples=40)
@given(a=st.lists(st.integers(min_value=1, max_value=400),
                  min_size=60, max_size=140))
def test_self_correlation_has_a_perfect_zero_offset_row(a):
    assume(len(set(a)) > 3)
    sa = classes.Sequence({'KeyCode': 'a', 'measurements': list(a)})
    sb = classes.Sequence({'KeyCode': 'b', 'measurements': list(a)})

    rows = classes.corellate(sa, sb, 999)    # all lags come back

    zero = [r for r in rows if r[7] == 0]
    assert zero and abs(zero[0][0] - 1.0) < 1e-9   # raw cc at offset 0 is 1
