"""Crossdating tests on the real MIL fixtures in ``testy/data``.

Each MIL fixture pair is two radii of one fir tree (matching ``drzUnikalne``),
the ``-d`` and ``-g`` sides, measured over the same calendar span.  Two radii of
one tree carry the same climate signal, so at their true (as-loaded) alignment
they must correlate strongly.  Local growth reductions on one radius (partial /
near-absent rings) are expected and are what the AA4-1-2 pair exercises.

    MIL-AA4-1-1a-d / -g   1946-2016, 71 rings   clean, r ~ 0.98
    MIL-U11-2-2-d  / -g   1872-2016, 145 rings  clean, r ~ 0.77
    MIL-AA4-1-2-d  / -g   1964-2016, 53 rings   4-year reduction on -g (four
                                                consecutive 1s) - raw r stays
                                                ~0.95 but the BP/H t-values
                                                collapse
"""
import os

import numpy as np
import pytest

import classes

DATA = os.path.join(os.path.dirname(__file__), 'data')

PAIRS = ['MIL-AA4-1-1a', 'MIL-U11-2-2', 'MIL-AA4-1-2']
CLEAN_PAIRS = ['MIL-AA4-1-1a', 'MIL-U11-2-2']


def load(stem):
    return classes.read_fh([os.path.join(DATA, stem + '.fh')])[stem]


def radii(pair):
    return load(pair + '-d'), load(pair + '-g')


# --------------------------------------------------------------------------
# the fixtures load with their rich Heidelberg metadata intact
# --------------------------------------------------------------------------

@pytest.mark.parametrize('pair', PAIRS)
def test_pair_members_describe_the_same_tree_over_the_same_span(pair):
    d, g = radii(pair)
    assert d.KeyCode() == pair + '-d'
    assert g.KeyCode() == pair + '-g'
    # two radii of one tree: identical calendar placement
    assert d.DateBegin() == g.DateBegin()
    assert d.DateEnd() == g.DateEnd()
    assert d.Length() == g.Length()
    # custom .fh header fields survive read_fh
    assert d.export_meta('drzUnikalne') == g.export_meta('drzUnikalne')
    assert d.export_meta('strona') == 'd'
    assert g.export_meta('strona') == 'g'
    assert d.export_meta('gat') == 'jd'          # jodla / silver fir


# --------------------------------------------------------------------------
# same-tree radii correlate strongly at their true alignment
# --------------------------------------------------------------------------

@pytest.mark.parametrize('pair,min_cc,min_glk,min_gsl', [
    ('MIL-AA4-1-1a', 0.90, 78, '***'),
    ('MIL-U11-2-2', 0.65, 63, '***'),
    # the reduction zone drags GLK down too, so AA4-1-2 only clears the 95%
    # (one star) Gleichlaeufigkeit threshold
    ('MIL-AA4-1-2', 0.88, 55, '*'),
])
def test_position_correlation_is_strong_and_significant(pair, min_cc, min_glk,
                                                        min_gsl):
    d, g = radii(pair)
    cc, tvbp, tvh, t, glk, gsl, cdi = classes.corellate_position(d, g)
    assert cc >= min_cc
    assert glk >= min_glk
    stars = ['', '*', '**', '***']
    assert stars.index(gsl) >= stars.index(min_gsl)
    assert t > 10


@pytest.mark.parametrize('pair', PAIRS)
def test_position_cc_field_equals_numpy_on_the_full_series(pair):
    d, g = radii(pair)
    cc = classes.corellate_position(d, g)[0]
    expected = round(float(np.corrcoef(d.measurements(), g.measurements())[0, 1]), 2)
    assert cc == expected


# --------------------------------------------------------------------------
# corellate auto-dates the clean pairs to offset 0
# --------------------------------------------------------------------------

@pytest.mark.parametrize('pair', CLEAN_PAIRS)
def test_corellate_best_hit_is_the_true_offset_zero(pair):
    d, g = radii(pair)
    rows = classes.corellate(d, g)
    best = rows[0]
    assert best[6] == max(r[6] for r in rows)     # really the CDI winner
    assert best[7] == 0                            # true offset
    assert best[8] == d.Length()                   # full overlap
    assert best[0] >= 0.70                         # crosscoef
    assert best[5] == '***'


@pytest.mark.parametrize('pair', CLEAN_PAIRS)
def test_corellate_is_direction_symmetric_for_the_pair(pair):
    d, g = radii(pair)
    fwd = classes.corellate(d, g)[0]
    rev = classes.corellate(g, d)[0]
    assert fwd[7] == 0 and rev[7] == 0
    assert fwd[0] == rev[0]                        # crosscoef
    assert fwd[4] == rev[4]                        # GLK


# --------------------------------------------------------------------------
# AA4-1-2: the growth-reduction pair - raw signal survives, BP/H does not
# --------------------------------------------------------------------------

def test_reduction_pair_keeps_raw_correlation_but_loses_bp_and_h():
    d, g = radii('MIL-AA4-1-2')
    # the -g radius nearly stops for four years (four consecutive 1s)
    assert g.measurements().count(1) >= 4

    rows = classes.corellate(d, g, count=10_000)
    at_zero = next(r for r in rows if r[7] == 0)
    assert at_zero[8] == d.Length()               # full overlap
    assert at_zero[0] >= 0.90                      # raw Pearson unbothered
    # BP and H divide by the near-zero rings -> huge outliers -> t collapses
    assert at_zero[1] < 3.0                        # TVBP
    assert at_zero[2] < 3.0                        # TVH


def test_reduction_pair_position_matches_the_offset_zero_row():
    d, g = radii('MIL-AA4-1-2')
    pos = classes.corellate_position(d, g)
    rows = classes.corellate(d, g, count=10_000)
    at_zero = next(r for r in rows if r[7] == 0)
    assert pos[0] == at_zero[0]                    # cc
    assert pos[4] == at_zero[4]                    # GLK
    assert pos[3] == at_zero[3]                    # plain T


# --------------------------------------------------------------------------
# crossdating discriminates the true alignment from a time-reversed one
# (all six samples are from one forest, so a *different-tree* control would
#  still correlate - the regional climate signal is real)
# --------------------------------------------------------------------------

@pytest.mark.parametrize('pair', PAIRS)
def test_true_alignment_beats_a_time_reversed_partner(pair):
    d, g = radii(pair)
    true_cc = classes.corellate_position(d, g)[0]
    g_reversed = classes.Sequence({
        'KeyCode': g.KeyCode() + 'R',
        'DateBegin': g.DateBegin(),
        'measurements': list(reversed(g.measurements())),
    })
    rev = classes.corellate_position(d, g_reversed)
    rev_cc = rev[0] if rev[0] != 'xxx' else 0.0
    assert true_cc > rev_cc + 0.3
