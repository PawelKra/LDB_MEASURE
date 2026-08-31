"""dendro.io - the format registry (S3.2) and the CSV / JSON exports (S4.2)."""
import csv

import pytest

import classes
from dendro import io as dio


def test_registry_lists_the_builtin_formats():
    assert 'fh' in dio.readable_extensions()
    assert 'pos' in dio.readable_extensions()
    assert 'rwl' in dio.readable_extensions()
    assert 'avr' in dio.readable_extensions()
    # pos has no writer; txt / csv have no reader
    assert 'pos' not in dio.writable_extensions()
    assert 'txt' not in dio.readable_extensions()
    assert 'csv' in dio.writable_extensions()


@pytest.mark.parametrize('path,expect', [
    ('dane_test/proba_a.fh', ['proba_a']),
    ('dane_test/deska1_3.pos', ['IMG_8409.JPG']),
    ('dane_test/STAR42.AVR', ['STAR42']),
    ('dane_test/LW11.R2', ['LW11']),
])
def test_read_dispatches_by_extension(path, expect):
    got = dio.read(path)
    assert sorted(got) == expect
    assert all(isinstance(s, classes.Sequence) for s in got.values())


def test_read_rwl_multi_via_registry():
    import os
    got = dio.read(os.path.join(os.path.dirname(__file__), 'data', 'multi.rwl'))
    assert sorted(got) == ['MULTI_AA', 'MULTI_BB', 'MULTI_CC']


def test_write_dispatches_and_round_trips(tmp_path):
    src = dio.read('dane_test/proba_a.fh')
    p = tmp_path / 'out.fh'
    dio.write(str(p), src)
    back = dio.read(str(p))
    assert back['proba_a'].measurements() == src['proba_a'].measurements()


def test_single_series_writer_adapter(tmp_path):
    seq = classes.Sequence({'KeyCode': 'S', 'DateBegin': 1,
                            'measurements': list(range(20, 101))})
    p = tmp_path / 'S.avr'
    dio.write(str(p), {'S': seq})          # dict in, one-file-per-series out
    back = dio.read(str(p))
    assert back['S'].measurements() == seq.measurements()


def test_unknown_extension_raises(tmp_path):
    with pytest.raises(ValueError):
        dio.read(str(tmp_path / 'x.unknown'))
    with pytest.raises(ValueError):
        dio.write(str(tmp_path / 'x.pos'), {})   # pos has no writer


# --- CSV / JSON export (S4.2) --------------------------------------

SEQS = {
    'A': classes.Sequence({'KeyCode': 'A', 'DateBegin': 1990,
                           'measurements': [10, 20, 30, 0, 50]}),
    'B': classes.Sequence({'KeyCode': 'B', 'DateBegin': 1992,
                           'measurements': [11, 22, 33]}),
}


def test_write_csv_is_a_year_by_sample_matrix(tmp_path):
    p = tmp_path / 'm.csv'
    dio.write(str(p), SEQS)
    with open(p, newline='') as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == ['year', 'A', 'B']
    assert rows[1] == ['1990', '10', '']          # B not started yet
    assert rows[3] == ['1992', '30', '11']         # overlap
    assert rows[4] == ['1993', '0', '22']          # a real 0 ring, not a gap
    assert rows[-1] == ['1994', '50', '33']
    assert len(rows) == 1 + (1994 - 1990 + 1)


def test_write_json_round_trips(tmp_path):
    p = tmp_path / 'm.json'
    dio.write(str(p), SEQS)
    back = dio.read(str(p))
    assert back['A'].DateBegin() == 1990
    assert back['A'].measurements() == [10, 20, 30, 0, 50]
    assert back['B'].DateBegin() == 1992
    assert back['B'].measurements() == [11, 22, 33]
    assert back['A'].KeyCode() == 'A'
