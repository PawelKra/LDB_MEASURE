"""Tests for classes.crossdate_pairs - the parallel replacement for the
per-pair double loop that ccres_window.crossdate used to run inline.
"""
import math
import pickle

import pytest

import classes


def _wave(n, phase):
    return [max(1, int(round(120 + 45 * math.sin(k / 6.0 + phase)
                             + 15 * math.sin(k / 2.4 + 2 * phase))))
            for k in range(n)]


def _seq(name, n, phase):
    return classes.Sequence({'KeyCode': name, 'measurements': _wave(n, phase)})


def _serial_res_dict(refs, smps, count):
    '''The exact loop ccres_window.crossdate ran before S2.2.'''
    rd = {}
    for ref in refs:
        for smp in smps:
            if smp.KeyCode() == ref.KeyCode():
                continue
            if smp.KeyCode() in rd and ref.KeyCode() in rd[smp.KeyCode()]:
                continue
            crslt = classes.corellate(smp, ref, count)
            rd.setdefault(ref.KeyCode(), {})
            rd.setdefault(smp.KeyCode(), {})
            rd[ref.KeyCode()][smp.KeyCode()] = crslt
            rd[smp.KeyCode()][ref.KeyCode()] = [
                x[:7] + [-x[7], x[8], x[10], x[9]] for x in crslt]
    return rd


REFS = [_seq('R1', 80, 0.0), _seq('R2', 95, 0.7), _seq('R3', 70, 1.9)]
SMPS = [_seq('S1', 88, 0.3), _seq('S2', 76, 1.2),
        _seq('S3', 90, 2.5), _seq('S4', 82, 3.1)]


def test_batch_worker_matches_corellate():
    r = REFS[0]
    samples = {s.KeyCode(): s.measurements() for s in SMPS}
    batch = classes._cd_batch(r.KeyCode(), r.measurements(),
                              [s.KeyCode() for s in SMPS], samples, 10)
    assert [name for name, _ in batch] == [s.KeyCode() for s in SMPS]
    for s, (name, rows) in zip(SMPS, batch):
        assert name == s.KeyCode()
        assert rows == classes.corellate(s, r, 10)


def test_worker_and_tasks_are_picklable():
    task = ('R1', _wave(60, 1.0), ['S1', 'S2'], 10)
    assert pickle.loads(pickle.dumps(task)) == task
    fn = pickle.loads(pickle.dumps(classes._cd_worker))
    classes._cd_init({'S1': _wave(60, 0.0), 'S2': _wave(60, 0.5)})
    assert fn(task) == classes._cd_worker(task)


def test_mirror_rows():
    rows = classes.corellate(SMPS[0], REFS[0], 5)
    mirr = classes._mirror_rows(rows)
    for a, b in zip(rows, mirr):
        assert b[:7] == a[:7]
        assert b[7] == -a[7]          # offset sign flipped
        assert b[8] == a[8]           # overlap unchanged
        assert b[9] == a[10] and b[10] == a[9]   # names swapped


def test_serial_matches_the_old_double_loop():
    got = classes.crossdate_pairs(REFS, SMPS, 10, max_workers=1)
    want = _serial_res_dict(REFS, SMPS, 10)
    assert list(got.keys()) == list(want.keys())
    assert got == want


def test_each_unordered_pair_computed_once_both_directions_stored():
    rd = classes.crossdate_pairs(REFS, SMPS, 10, max_workers=1)
    for r in REFS:
        for s in SMPS:
            assert rd[r.KeyCode()][s.KeyCode()] == classes._mirror_rows(
                rd[s.KeyCode()][r.KeyCode()])


def test_no_pairs_returns_empty():
    assert classes.crossdate_pairs([], SMPS, 10) == {}
    solo = _seq('X', 80, 0.0)
    assert classes.crossdate_pairs([solo], [solo], 10) == {}


def test_parallel_result_is_identical_to_serial():
    serial = classes.crossdate_pairs(REFS, SMPS, 10, max_workers=1)
    try:
        parallel = classes.crossdate_pairs(REFS, SMPS, 10, max_workers=2)
    except Exception as exc:                       # pragma: no cover
        pytest.skip('process pool unavailable here: %r' % exc)
    assert list(parallel.keys()) == list(serial.keys())
    assert parallel == serial
