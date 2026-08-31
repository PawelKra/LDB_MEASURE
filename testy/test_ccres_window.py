"""The crossdating result window (``ccres_window.Results``) and its little
options dialog (``ccopt_window.Options``).

Complements ``test_cc_window.py`` - here: the grouping modes, the chart
redraw on row click, the colour toggle, applying a pick, and cancelling.
"""
import os

import pytest
from PyQt6.QtGui import QColor

import classes
from ccopt_window import Options
from ccres_window import Results

FILES = ['dane_test/proba_a.fh', 'dane_test/proba_b.fh', 'dane_test/deska1_3.fh']


@pytest.fixture
def crossdated(qtbot, no_modals):
    """A ``Results`` window with the three fixture samples already crossdated."""
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(FILES)
    f1['proba_a'].setDateBegin(1688)
    st.add_seq('s', f1)

    win = Results(st)
    qtbot.addWidget(win)
    win.choose_cc_job(allcc=True)
    win.crossdate()
    return win


# --- Options dialog ------------------------------------------------

def test_options_ok_clears_cancel_flag(qtbot, no_modals):
    opt = Options()
    qtbot.addWidget(opt)
    assert opt.cancel is True

    opt.ok()

    assert opt.cancel is False


def test_options_cancel_keeps_cancel_flag(qtbot, no_modals):
    opt = Options()
    qtbot.addWidget(opt)

    opt.cancelm()

    assert opt.cancel is True


# --- grouping modes ---------------------------------------------

def test_group_by_reference_is_the_default(crossdated):
    crossdated.grp = 0
    crossdated.load_result()
    assert 'proba_a' in crossdated.out_dict            # keyed by reference


def test_group_by_sample(crossdated):
    crossdated.grp = 1
    crossdated.load_result()
    # every key is a sample name, every value a formatted block
    assert crossdated.out_dict
    assert all(isinstance(v, list) and v for v in crossdated.out_dict.values())


def test_group_by_none(crossdated):
    crossdated.grp = 2
    crossdated.load_result()
    assert crossdated.out_dict


def test_load_result_fills_the_table(crossdated):
    crossdated.load_result()
    assert crossdated.ui.tableWidget_results.rowCount() == len(crossdated.result)
    assert crossdated.result[0].startswith('----------')


# --- chart redraw on selection --------------------------------

def test_redraw_plots_reference_and_sample(crossdated):
    crossdated.load_result()
    crossdated.ui.tableWidget_results.item(8, 0).setSelected(True)

    crossdated.redraw()

    assert len(crossdated.ui.widget.canvas.ax.lines) == 2      # ref + sample


def test_redraw_without_selection_is_a_noop(crossdated):
    crossdated.load_result()
    crossdated.ui.widget.canvas.ax.clear()
    crossdated.redraw()                       # nothing selected -> IndexError guard
    assert len(crossdated.ui.widget.canvas.ax.lines) == 0


# --- colour toggle on double click --------------------------

def test_double_click_toggles_row_highlight(crossdated):
    crossdated.load_result()
    red = QColor(255, 0, 0, 127).getRgb()
    tw = crossdated.ui.tableWidget_results

    crossdated.ui.tableWidget_results.cellDoubleClicked.emit(8, 0)
    assert tw.item(8, 0).background().color().getRgb() == red

    crossdated.ui.tableWidget_results.cellDoubleClicked.emit(8, 0)
    assert tw.item(8, 0).background().color().getRgb() != red


# --- applying a pick / cancelling --------------------------

def test_make_permanent_writes_back_the_new_datebegin(crossdated):
    crossdated.load_result()
    tw = crossdated.ui.tableWidget_results

    crossdated.ui.tableWidget_results.cellDoubleClicked.emit(8, 0)   # mark red
    sname = tw.item(8, 0).text().split()[0]
    before = crossdated.stack.get('s', sname).DateBegin()

    crossdated.make_permanent()

    assert crossdated.stack.get('s', sname).DateBegin() != before
    assert crossdated.changed is True


def test_cancel_hides_the_window(crossdated):
    crossdated.show()
    crossdated.cancel()
    assert crossdated.isHidden()


def test_save_txt_writes_report(crossdated, tmp_path):
    crossdated.load_result()
    out = tmp_path / 'report.txt'

    crossdated.save_txt(p2f=str(out))

    assert out.exists() and out.read_text().strip()


def test_save_txt_with_empty_path_does_nothing(crossdated):
    crossdated.load_result()
    crossdated.save_txt(p2f='')          # must not raise
