"""Golden test pinning the output of ``corellate`` / ``corellate_position``.

The reference values in ``data/corellate_golden.json`` are the contract for
the P1-P3 vectorisation work: those phases must reproduce this file byte for
byte after rounding. Regenerate deliberately (and review the diff) with::

    python3 testy/test_corellate_golden.py

Run from the repository root (the fixtures live in ``dane_test/``).
"""
import json
import math
import os
import sys

import pytest  # noqa

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import classes  # noqa: E402

GOLDEN = os.path.join(os.path.dirname(__file__), 'data', 'corellate_golden.json')

# rounding applied to every float before comparison / storage
_NDIGITS = 6


def _synth(n, phase):
    """Deterministic pseudo ring-widths - no RNG, stable across platforms."""
    out = []
    for k in range(n):
        v = (150.0
             + 60.0 * math.sin(k / 7.0 + phase)
             + 25.0 * math.sin(k / 2.3 + 2.0 * phase)
             + (k % 5) * 4.0
             + ((k * k) % 11) - 5.0)
        out.append(int(round(abs(v))) + 20)
    return out


def _sequences():
    """Named Sequence objects used by the cases below."""
    fh = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh'])
    seqs = {
        'proba_a': fh['proba_a'],
        'proba_b': fh['proba_b'],
        'deska': fh['IMG_8409.JPG'],
        'synth_a': classes.Sequence({'KeyCode': 'synth_a', 'DateBegin': 1,
                                     'measurements': _synth(150, 0.0)}),
        'synth_b': classes.Sequence({'KeyCode': 'synth_b', 'DateBegin': 1,
                                     'measurements': _synth(110, 0.3)}),
    }
    return seqs


# (sample, reference) name pairs
_CORELLATE_PAIRS = [
    ('proba_a', 'proba_b'),
    ('proba_b', 'proba_a'),
    ('proba_a', 'deska'),
    ('deska', 'proba_b'),
    ('synth_a', 'synth_b'),
]

# (a, b, DateBegin_a, DateBegin_b) - positions chosen for >= 30 years overlap
_POSITION_PAIRS = [
    ('proba_a', 'proba_b', 1688, 1745),
    ('proba_a', 'deska', 1, 1),
    ('synth_a', 'synth_b', 1000, 1000),
]


def _canon(value):
    """Round floats, recurse into lists, leave ints/strings alone.

    Non-finite floats become an explicit marker so the file stays valid,
    strict JSON and mismatches read clearly.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return '<nan>'
        if math.isinf(value):
            return '<inf>' if value > 0 else '<-inf>'
        return round(value, _NDIGITS)
    if isinstance(value, (list, tuple)):
        return [_canon(v) for v in value]
    return value


def _compute():
    seqs = _sequences()
    out = {'corellate': {}, 'corellate_position': {}}

    for sname, rname in _CORELLATE_PAIRS:
        key = sname + '__' + rname
        rows = classes.corellate(seqs[sname], seqs[rname])
        out['corellate'][key] = _canon(rows)

    for aname, bname, dba, dbb in _POSITION_PAIRS:
        key = aname + '__' + bname
        fresh = _sequences()
        a, b = fresh[aname], fresh[bname]
        a.setDateBegin(dba)
        b.setDateBegin(dbb)
        out['corellate_position'][key] = _canon(classes.corellate_position(a, b))

    return out


def _load_golden():
    with open(GOLDEN, 'r') as fh:
        return _canon(json.load(fh))


@pytest.mark.parametrize('section', ['corellate', 'corellate_position'])
def test_golden(section):
    if not os.path.exists(GOLDEN):
        pytest.skip('golden file missing - run this module as a script first')
    expected = _load_golden()[section]
    actual = _compute()[section]
    assert set(actual) == set(expected)
    for key in expected:
        assert actual[key] == expected[key], key


if __name__ == '__main__':
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
    with open(GOLDEN, 'w') as fh:
        json.dump(_compute(), fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('wrote', GOLDEN)
