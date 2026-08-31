"""End-to-end behaviour of the crossdating entry points.

``corellate``          - slides a sample past a reference, returns the best
                         ``count`` alignments ranked by CDI.
``corellate_position`` - statistics for two Sequences at their current
                         (DateBegin) alignment.

These tests pin the observable contract: schema, ordering, offset recovery,
swap behaviour and the overlap gate.  They complement
``test_corellate_golden.py`` (fixed numeric snapshot) and
``test_corellate_reference.py`` (statistics vs their textbook definitions).
"""
import math

import numpy as np
import pytest

import classes

ROW_LEN = 11
# [cc, TVBP, TVH, T, GLK, GSL, CDI, offset, ovl, sample_name, ref_name]


def wave(n, phase, amp=46.0):
    return [138.0
            + amp * math.sin(k / 6.1 + phase)
            + 15.0 * math.sin(k / 2.6 + 1.9 * phase)
            + 0.09 * k
            for k in range(n)]


def jitter(values, scale=1.5):
    """Deterministic small perturbation - keeps r high but below 1."""
    return [v + scale * math.sin(i * 2.3999632 + 0.5) for i, v in enumerate(values)]


def seq(name, data, date_begin=1000):
    return classes.Sequence({'KeyCode': name, 'DateBegin': date_begin,
                             'measurements': list(data)})


# --------------------------------------------------------------------------
# corellate: schema / ordering / count
# --------------------------------------------------------------------------

def test_row_schema_and_types():
    rows = classes.corellate(seq('S', wave(70, 0.7)), seq('R', wave(140, 0.2)))
    assert rows and all(len(r) == ROW_LEN for r in rows)
    r = rows[0]
    assert isinstance(r[0], float)                     # crosscoef
    assert isinstance(r[1], (int, float))              # TVBP
    assert isinstance(r[2], (int, float))              # TVH
    assert isinstance(r[3], (int, float))              # T
    assert isinstance(r[4], (int, float))              # GLK
    assert isinstance(r[5], str) and r[5] in ('', '*', '**', '***')
    assert isinstance(r[6], int)                       # CDI
    assert isinstance(r[7], int)                       # offset
    assert isinstance(r[8], int)                       # overlap
    assert r[9] == 'S' and r[10] == 'R'


def test_rows_sorted_by_cdi_descending():
    rows = classes.corellate(seq('S', wave(80, 1.1)), seq('R', wave(200, 0.4)),
                             count=25)
    cdis = [r[6] for r in rows]
    assert cdis == sorted(cdis, reverse=True)


@pytest.mark.parametrize('count', [1, 3, 10, 50])
def test_count_caps_number_of_rows(count):
    rows = classes.corellate(seq('S', wave(90, 0.9)), seq('R', wave(260, 0.1)),
                             count=count)
    assert len(rows) <= count


def test_default_count_is_ten():
    rows = classes.corellate(seq('S', wave(90, 0.9)), seq('R', wave(260, 0.1)))
    assert len(rows) == 10


# --------------------------------------------------------------------------
# corellate: offset recovery
# --------------------------------------------------------------------------

@pytest.mark.parametrize('k', [25, 40, 70, 110])
def test_recovers_offset_of_embedded_window(k):
    ref = wave(200, 0.35)
    window = 60
    assert 0 < k and k + window - 1 < len(ref)
    sample = jitter(ref[k:k + window])          # noisy copy of ref[k : k+window]
    best = classes.corellate(seq('S', sample), seq('R', ref), count=1)[0]
    assert best[7] == k                          # offset field
    assert best[0] >= 0.9                        # crosscoef near 1


def test_self_match_produces_a_perfect_zero_offset_row():
    x = wave(120, 1.4)
    rows = classes.corellate(seq('X', x), seq('X', x), count=10_000)
    perfect = [r for r in rows if r[7] == 0]
    assert perfect, 'no zero-offset alignment returned'
    row = perfect[0]
    assert row[0] == 1.0        # crosscoef
    assert row[4] == 100        # GLK - every interval agrees
    assert row[8] == len(x)     # full overlap


# --------------------------------------------------------------------------
# corellate: behaviour under sample/reference swap
# --------------------------------------------------------------------------

def test_swap_negates_offset_and_preserves_r_and_glk():
    a = wave(85, 0.0)
    b = wave(150, 0.0)                           # b contains a's shape at k=0..
    fwd = classes.corellate(seq('A', a), seq('B', b), count=10_000)
    rev = classes.corellate(seq('B', b), seq('A', a), count=10_000)
    rev_by_off = {r[7]: r for r in rev}
    checked = 0
    for r in fwd:
        mate = rev_by_off.get(-r[7])
        if mate is None:
            continue
        checked += 1
        assert r[0] == pytest.approx(mate[0], abs=0.01)   # crosscoef
        assert abs(r[4] - mate[4]) <= 1                    # GLK (ovl may differ
        #                                                    by 1 at a boundary)
    assert checked >= 20


# --------------------------------------------------------------------------
# corellate_position
# --------------------------------------------------------------------------

def test_position_rejects_non_sequence():
    assert classes.corellate_position([1, 2, 3], seq('B', wave(40, 0))) is False
    assert classes.corellate_position(seq('A', wave(40, 0)), None) is False


def test_position_swap_is_invariant():
    a = seq('A', wave(90, 0.0), date_begin=1400)
    b = seq('B', wave(90, 1.2), date_begin=1400)
    assert classes.corellate_position(a, b) == classes.corellate_position(b, a)


@pytest.mark.parametrize('overlap', [5, 15, 29])
def test_position_returns_xxx_below_thirty_year_overlap(overlap):
    n = 40
    a = seq('A', wave(n, 0.0), date_begin=1000)
    b = seq('B', wave(n, 0.5), date_begin=1000 + (n - overlap))
    assert classes.corellate_position(a, b) == ['xxx'] * 7


@pytest.mark.parametrize('shift', [0, 20, 45])
def test_position_cc_matches_direct_corr_on_the_shared_overlap(shift):
    n = 90
    x = wave(n, 0.0)
    y = wave(n, 1.3)
    a = seq('A', x, date_begin=1000)
    b = seq('B', y, date_begin=1000 + shift)
    res = classes.corellate_position(a, b)
    # older sample is the reference; the loop pairs younger[i] with older[i+shift]
    ox = y[:n - shift]
    oy = x[shift:]
    expected = round(float(np.corrcoef(ox, oy)[0, 1]), 2)
    assert res[0] == expected


# --------------------------------------------------------------------------
# the numpy pieces the module actually relies on
# --------------------------------------------------------------------------

def test_glk_add_counter_mechanism_matches_manual_count():
    from collections import Counter
    from numpy import add

    x = wave(75, 0.0)
    y = wave(75, 2.4)
    gx = [1 if b - a >= 0 else 0 for a, b in zip(x, x[1:])]
    gy = [1 if b - a >= 0 else 0 for a, b in zip(y, y[1:])]

    combined = list(add(gx, gy))                 # element-wise, 0 / 1 / 2
    glk = Counter(combined)[0] + Counter(combined)[2]

    manual = sum(1 for p, q in zip(gx, gy) if p == q)
    assert glk == manual
    assert set(combined) <= {0, 1, 2}


def test_corrcoef_offdiagonal_is_the_reported_crosscoef():
    x = wave(64, 0.0)
    y = wave(64, 1.1)
    res = classes.corellate_position(seq('X', x), seq('Y', y))
    assert res[0] == round(float(np.corrcoef(x, y)[0, 1]), 2)


# --------------------------------------------------------------------------
# real Heidelberg fixtures
# --------------------------------------------------------------------------

def test_real_fixture_pair_matches_golden_top_row():
    fh = classes.read_fh(['dane_test/proba_a.fh', 'dane_test/proba_b.fh'])
    rows = classes.corellate(fh['proba_a'], fh['proba_b'])
    top = rows[0]
    # values pinned in test_corellate_golden.json / test_klasy.test_corellate
    assert top[0] == 0.62
    assert top[2] == 3.5
    assert top[4:7] == [70, '**', 21]
    assert top[7] == -57
    assert top[8] == 57
    assert top[9:] == ['proba_a', 'proba_b']
