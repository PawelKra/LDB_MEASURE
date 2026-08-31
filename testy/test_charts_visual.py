"""Image-regression tests for the chart (pytest-mpl).

These render the *real* widget figure and diff it against a committed
baseline PNG, catching visual regressions that the structural assertions in
test_panel_chart.py can't see (overlapping labels, a stray year-0 tick,
the sapwood trace drawn in the wrong place, clipped axes...).

Baselines live in testy/baseline/ and were generated in the `ldb` env:

    pytest testy/test_charts_visual.py --mpl-generate-path=testy/baseline

Run the comparison with:  pytest --mpl
Without --mpl the test bodies still execute (so a crash is still caught),
they just skip the pixel diff.

tolerance is deliberately loose - a matplotlib / freetype bump should not
turn into a red build; a real layout change will still blow past it.
"""
import pytest

import classes

MPL = dict(baseline_dir='baseline', tolerance=25,
           savefig_kwargs={'dpi': 80})


def _fig(win):
    win.redraw_chart()
    return win.ui.widget.canvas.figure


@pytest.mark.mpl_image_compare(**MPL)
def test_main_chart_three_samples(loaded_window):
    return _fig(loaded_window)


@pytest.mark.mpl_image_compare(**MPL)
def test_main_chart_with_sapwood(loaded_window):
    loaded_window.stack.base['s']['R1'].set_meta('SapWood', 40)
    return _fig(loaded_window)


@pytest.mark.mpl_image_compare(**MPL)
def test_main_chart_spanning_the_bc_ad_boundary(main_window):
    win = main_window
    a = classes.Sequence({'KeyCode': 'A', 'DateBegin': -60,
                          'measurements': [80 + (k * 7) % 60 for k in range(120)]})
    b = classes.Sequence({'KeyCode': 'B', 'DateBegin': -30,
                          'measurements': [90 + (k * 5) % 50 for k in range(110)]})
    win.stack.add_seq('s', {'A': a, 'B': b})
    win.order = ['A', 'B']
    return _fig(win)
