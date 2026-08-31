"""Cross-check LDB's crossdating statistics against their commonly accepted
definitions, using numpy as an independent oracle (scipy is not a project
dependency).

Accepted references
-------------------
* Pearson r                  numpy.corrcoef
* t value of a correlation   Student's t, df = n - 2:  r*sqrt(n-2)/sqrt(1-r**2)
* TVBP                        Baillie & Pilcher 1973 - each ring as a fraction
                             of the centred 5-year mean, then log
* TVH                         Hollstein 1980 - log ratio of successive rings
* GLK / Gleichlaeufigkeit     Eckstein & Bauch 1969
* GSL                         G >= 50 + z * 50/sqrt(n), z ~ 1.65 / 2.33 / 3.09
* CDI                         TSAP-Win Cross-Date Index

Two deliberate LDB simplifications are pinned here - the current behaviour is
asserted and the deviation from the textbook is documented in the test:
  1. GLK treats "no change" as an increase and gives no half credit on a tie.
  2. The BP / H transforms drop constant factors (log base, x100, series
     direction) - harmless for a correlation, so r / t are unaffected.
"""
import math

import numpy as np
import pytest

import classes


# --------------------------------------------------------------------------
# deterministic, tie-free synthetic ring series (floats -> no integer ties)
# --------------------------------------------------------------------------

def wave(n, phase, amp=48.0):
    return [140.0
            + amp * math.sin(k / 6.3 + phase)
            + 17.0 * math.sin(k / 2.7 + 1.7 * phase)
            + 0.11 * k
            for k in range(n)]


def seq(name, data, date_begin=1000):
    return classes.Sequence({'KeyCode': name, 'DateBegin': date_begin,
                             'measurements': list(data)})


def position_stats(x, y):
    """Run corellate_position on two equal-length series aligned 1:1 and
    return [cc, TVBP, TVH, T, GLK, GSL, CDI]."""
    res = classes.corellate_position(seq('x', x), seq('y', y))
    assert res[0] != 'xxx', 'overlap below 30 - widen the test series'
    return res


# --------------------------------------------------------------------------
# independent reference implementations
# --------------------------------------------------------------------------

def ref_pearson(x, y):
    return float(np.corrcoef(np.asarray(x, float), np.asarray(y, float))[0, 1])


def ref_student_t(r, n):
    return r * math.sqrt(n - 2) / math.sqrt(1.0 - r * r)


def _bp_ratios(v):
    v = np.asarray(v, float)
    return [v[i] / v[i - 2:i + 3].mean() for i in range(2, len(v) - 2)]


def ref_bp(v):
    """Baillie & Pilcher: ring / centred 5-year mean, logged."""
    return [math.log(r) for r in _bp_ratios(v)]


def ref_hollstein(v):
    """Hollstein: log ratio of successive rings (LDB uses log10 and the ratio
    to the *next* ring; both are constant transforms that cancel in r)."""
    v = np.asarray(v, float)
    return [math.log10(v[i] / v[i + 1]) for i in range(len(v) - 1)]


def ref_glk_simple(x, y):
    """LDB definition: flat counts as 'up', agreement = identical binary
    direction, expressed as a percentage of the n-1 intervals."""
    gx = (np.diff(np.asarray(x, float)) >= 0).astype(int)
    gy = (np.diff(np.asarray(y, float)) >= 0).astype(int)
    return round(np.count_nonzero(gx == gy) / (len(x) - 1) * 100)


def ref_glk_eckstein_bauch(x, y):
    """Textbook GLK: +/- 1/2 per interval, 0 on no change, so a tie against a
    moving interval scores half."""
    step = lambda d: 0.5 if d > 0 else (-0.5 if d < 0 else 0.0)
    dx = [step(b - a) for a, b in zip(x, x[1:])]
    dy = [step(b - a) for a, b in zip(y, y[1:])]
    return sum(1.0 - abs(p - q) for p, q in zip(dx, dy)) / (len(x) - 1) * 100


def ref_gsl(glk_pct, n):
    fr1 = 50 + 82.7 / math.sqrt(n)
    fr2 = 50 + 116.3 / math.sqrt(n)
    fr3 = 50 + 154.0 / math.sqrt(n)
    if glk_pct >= fr3:
        return '***'
    if glk_pct >= fr2:
        return '**'
    if glk_pct >= fr1:
        return '*'
    return ''


def ref_cdi(glk_pct, section, sample_len, tvbp, tvh):
    tmean = (tvbp + tvh) / 2.0
    val = (((glk_pct - 50) + 50 * math.sqrt(section / sample_len)) * tmean) / 10
    return round(val, 0) if val < 1000 else 1000


# --------------------------------------------------------------------------
# Pearson r  and  plain t
# --------------------------------------------------------------------------

@pytest.mark.parametrize('phase', [0.0, 0.5, 1.3, 2.6, 4.0])
def test_pearson_r_matches_numpy(phase):
    x, y = wave(90, 0.0), wave(90, phase)
    cc = position_stats(x, y)[0]
    assert cc == round(ref_pearson(x, y), 2)


@pytest.mark.parametrize('phase', [0.2, 0.9, 1.8, 3.1])
def test_plain_t_is_student_t_of_r(phase):
    x, y = wave(96, 0.0), wave(96, phase)
    t = position_stats(x, y)[3]
    n = len(x)
    assert t == round(ref_student_t(ref_pearson(x, y), n), 1)


@pytest.mark.parametrize('n', [8, 15, 30, 64, 128, 300])
@pytest.mark.parametrize('r', [-0.95, -0.4, -0.05, 0.0, 0.2, 0.37, 0.6, 0.88, 0.97])
def test_T_helper_equals_student_formula(n, r):
    assert classes._T(n, r) == pytest.approx(ref_student_t(r, n), rel=1e-12,
                                             abs=1e-12)


@pytest.mark.parametrize('n,r', [(50, 1.0), (50, 1.0000001), (50, 1.5),
                                 (1, 0.5)])
def test_T_helper_degenerate_guard_returns_one(n, r):
    # r >= 1 (float noise or a perfect match) or n < 2 -> sqrt of a negative.
    # LDB returns 1 rather than crashing, matching the ZeroDivisionError branch.
    assert classes._T(n, r) == 1


def test_T_helper_zero_at_n_equals_2():
    # sqrt(n - 2) == 0, no exception: a real 0, not the guard value
    assert classes._T(2, 0.5) == 0.0


# --------------------------------------------------------------------------
# Baillie & Pilcher  (TVBP)  and  Hollstein  (TVH)
# --------------------------------------------------------------------------

@pytest.mark.parametrize('phase', [0.3, 1.1, 2.2, 3.7])
def test_tvbp_matches_baillie_pilcher(phase):
    x, y = wave(100, 0.0), wave(100, phase)
    tvbp = position_stats(x, y)[1]
    bx, by = ref_bp(x), ref_bp(y)          # length L-4
    assert tvbp == round(ref_student_t(ref_pearson(bx, by), len(bx)), 1)


@pytest.mark.parametrize('phase', [0.3, 1.1, 2.2, 3.7])
def test_tvh_matches_hollstein(phase):
    x, y = wave(100, 0.0), wave(100, phase)
    tvh = position_stats(x, y)[2]
    # LDB drops the first transformed value (standHa[1:]) -> length L-2
    hx, hy = ref_hollstein(x)[1:], ref_hollstein(y)[1:]
    assert tvh == round(ref_student_t(ref_pearson(hx, hy), len(hx)), 1)


def test_bp_dropped_x100_constant_does_not_change_r():
    x, y = wave(80, 0.0), wave(80, 1.4)
    ratios = _bp_ratios(x)
    bp_plain = [math.log(r) for r in ratios]
    bp_x100 = [math.log(100 * r) for r in ratios]
    by = ref_bp(y)
    assert ref_pearson(bp_plain, by) == pytest.approx(ref_pearson(bp_x100, by),
                                                      abs=1e-12)


def test_hollstein_log_base_and_direction_cancel_in_r():
    # switching log base (10 -> e) and ratio direction (next -> previous ring)
    # only flips the sign / rescales each element, so |r| is unchanged.
    x, y = wave(80, 0.0), wave(80, 2.1)
    v = np.asarray(x, float)
    log10_next = [math.log10(v[i] / v[i + 1]) for i in range(len(v) - 1)]
    ln_prev = [math.log(v[i] / v[i - 1]) for i in range(1, len(v))]
    hy = ref_hollstein(y)
    assert abs(ref_pearson(log10_next, hy)) == pytest.approx(
        abs(ref_pearson(ln_prev, hy)), abs=1e-9)


# --------------------------------------------------------------------------
# GLK / Gleichlaeufigkeit  and  GSL
# --------------------------------------------------------------------------

@pytest.mark.parametrize('phase', [0.4, 1.0, 2.0, 3.3, 5.0])
def test_glk_matches_simple_direction_count(phase):
    x, y = wave(85, 0.0), wave(85, phase)
    assert 0 not in np.sign(np.diff(x)) and 0 not in np.sign(np.diff(y))
    glk = position_stats(x, y)[4]
    assert glk == ref_glk_simple(x, y)


@pytest.mark.parametrize('phase', [0.4, 1.0, 2.0, 3.3])
def test_glk_agrees_with_eckstein_bauch_when_no_ties(phase):
    # on strictly monotone-between-points data the LDB shortcut and the
    # textbook GLK land within one rounding step of each other
    x, y = wave(85, 0.0), wave(85, phase)
    assert ref_glk_simple(x, y) == pytest.approx(
        ref_glk_eckstein_bauch(x, y), abs=1.0)


def test_glk_deviates_from_eckstein_bauch_on_ties():
    # consecutive equal ring widths do occur in 1/100 mm data; LDB scores a
    # tie-vs-rising interval as full agreement, the textbook scores it 1/2.
    x = [10, 10, 12, 12, 11, 13, 13, 13, 14, 12,
         12, 15, 16, 16, 14, 14, 17, 18, 18, 16] * 2
    y = [11, 11, 11, 13, 12, 12, 14, 14, 13, 13,
         15, 15, 14, 16, 16, 15, 15, 17, 17, 17] * 2
    simple = ref_glk_simple(x, y)
    textbook = ref_glk_eckstein_bauch(x, y)
    assert simple != pytest.approx(textbook, abs=1.0)
    # the shipping code follows the simplified definition
    assert position_stats(x, y)[4] == simple


@pytest.mark.parametrize('phase', [i * 0.17 for i in range(24)])
def test_gsl_stars_follow_published_thresholds(phase):
    x = wave(60 + int(phase * 7), 0.0, amp=12 + phase)
    y = wave(60 + int(phase * 7), phase + 0.8, amp=30)
    res = classes.corellate_position(seq('x', x), seq('y', y))
    if res[0] == 'xxx':
        pytest.skip('overlap < 30')
    n = min(len(x), len(y))
    assert res[5] == ref_gsl(res[4], n)


# --------------------------------------------------------------------------
# CDI  (TSAP-Win Cross-Date Index)
# --------------------------------------------------------------------------

@pytest.mark.parametrize('glk,section,slen,tbp,th', [
    (70, 80, 100, 5.0, 4.0),
    (55, 40, 260, 2.1, 1.8),
    (90, 120, 120, 8.4, 7.9),
    (48, 30, 300, 0.5, 0.7),
])
def test_cdi_matches_tsap_formula(glk, section, slen, tbp, th):
    assert classes.cdi(glk, section, slen, tbp, th) == ref_cdi(
        glk, section, slen, tbp, th)


def test_cdi_is_clamped_at_1000():
    assert classes.cdi(99, 100, 100, 500, 500) == 1000


@pytest.mark.parametrize('phase', [0.6, 1.5, 2.9])
def test_cdi_field_is_consistent_with_reported_components(phase):
    x, y = wave(110, 0.0), wave(110, phase)
    cc, tvbp, tvh, t, glk, gsl, cdi = position_stats(x, y)
    section = len(x)
    sample_len = min(len(x), len(y))
    assert cdi == int(ref_cdi(glk, section, sample_len, tvbp, tvh))
