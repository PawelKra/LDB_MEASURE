"""Calendar arithmetic has no year 0: 1 BC (-1) is immediately followed by
1 AD (+1). Every span / index / shift that crosses the era boundary must
skip the 0 slot.
"""
import pytest

import classes


# --- the primitives -------------------------------------------------

@pytest.mark.parametrize("begin, offset, year", [
    (5, 3, 8),           # wholly AD - unchanged
    (-8, 2, -6),         # wholly BC - unchanged
    (-3, 2, -1),         # last BC ring
    (-3, 3, 1),          # first AD ring - the 0 slot is skipped
    (-1, 1, 1),          # 1 BC then 1 AD, adjacent
    (-3, 4, 2),
])
def test_year_at_offset(begin, offset, year):
    assert classes._year_at_offset(begin, offset) == year
    # round-trips
    assert classes._offset_of_year(year, begin) == offset


@pytest.mark.parametrize("year, delta, out", [
    (1, -1, -1), (-1, 1, 1),          # step across the boundary
    (5, -1, 4), (-3, -1, -4),         # no crossing
    (2, -3, -2), (-2, 3, 2),          # crossing with a bigger step
])
def test_shift_year(year, delta, out):
    assert classes.shift_year(year, delta) == out


def test_year_span_never_contains_zero():
    span = classes.year_span(-4, 9)
    assert span == [-4, -3, -2, -1, 1, 2, 3, 4, 5]
    assert 0 not in span


# --- Sequence -----------------------------------------------------

def test_dateend_skips_year_zero():
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': -3,
                          'measurements': [10, 11, 12, 13, 14]})  # 5 rings
    assert s.years() == [-3, -2, -1, 1, 2]
    assert s.DateEnd() == 2                       # not 1


def test_measure_from_year_across_the_boundary():
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': -2,
                          'measurements': [10, 20, 30, 40]})       # -2,-1,1,2
    assert s.measure_from_year(-1) == 20
    assert s.measure_from_year(1) == 30
    assert s.measure_from_year(0) is False        # not a year


def test_setdatebegin_rejects_year_zero():
    s = classes.Sequence({'KeyCode': 'S', 'measurements': [1, 2, 3]})
    s.setDateBegin(0)
    assert s.DateBegin() == 1                     # bumped off the void


def test_setdateend_back_derives_across_the_boundary():
    s = classes.Sequence({'KeyCode': 'S', 'measurements': [1, 2, 3, 4, 5]})
    s.setDateEnd(2)                               # last ring is 2 AD
    assert s.years() == [-3, -2, -1, 1, 2]
    assert s.DateBegin() == -3


def test_construction_from_dateend_across_the_boundary():
    s = classes.Sequence({'KeyCode': 'S', 'DateEnd': 3,
                          'measurements': [1, 2, 3, 4, 5, 6]})     # 6 rings
    assert s.years() == [-3, -2, -1, 1, 2, 3]
    assert s.DateBegin() == -3


def test_add_and_delete_year_across_the_boundary():
    s = classes.Sequence({'KeyCode': 'S', 'DateBegin': -2,
                          'measurements': [10, 20, 30, 40]})       # -2,-1,1,2
    assert s.add_year_measurement(1, 99) is True
    assert s.years() == [-2, -1, 1, 2, 3]
    assert s.measurements() == [10, 20, 99, 30, 40]

    assert s.delete_year_measurement(1) is True
    assert s.measurements() == [10, 20, 30, 40]

    assert s.add_year_measurement(0, 5) is False  # year 0 is not addressable
    assert s.update_year_measurement(0, 5) is False
    assert s.delete_year_measurement(0) is False


def test_mean_across_the_boundary_has_no_year_zero_slot():
    db = classes.DataBase('s')
    db.add_seq('s', {
        'A': classes.Sequence({'KeyCode': 'A', 'DateBegin': -4,
                               'measurements': [10] * 9}),         # -4..5
        'B': classes.Sequence({'KeyCode': 'B', 'DateBegin': -2,
                               'measurements': [20] * 6}),         # -2..5
    })
    mean = db.calculate_mean('s', ['A', 'B'])

    assert 0 not in mean.years()
    assert mean.Length() == len(mean.years())
    assert mean.DateBegin() == -4
    assert mean.measure_from_year(0) is False
