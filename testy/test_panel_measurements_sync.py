"""``PanelMeasurements`` - the measures table <-> database sync
(``sync_twmeas_to_db``) and the guard paths of continue / crossdate.
"""
import pytest
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

import classes


def set_cell(win, row, col, text):
    tw = win.ui.tableWidget_meas
    tw.blockSignals(True)
    tw.setItem(row, col, QTableWidgetItem(str(text)))
    tw.blockSignals(False)
    tw.cellChanged.emit(row, col)


# --- sync_twmeas_to_db: one case per editable column ----------------

def test_datebegin_column_updates_db(loaded_window):
    set_cell(loaded_window, 0, 1, 812)
    assert loaded_window.stack.base['s']['R1'].DateBegin() == 812


def test_datebegin_column_reverts_bad_input(loaded_window):
    r1 = loaded_window.stack.base['s']['R1']
    good = r1.DateBegin()

    set_cell(loaded_window, 0, 1, 'not-a-year')

    assert r1.DateBegin() == good
    assert loaded_window.ui.tableWidget_meas.item(0, 1).text() == str(good)


def test_dateend_column_updates_db(loaded_window):
    r1 = loaded_window.stack.base['s']['R1']
    length = r1.Length()

    set_cell(loaded_window, 0, 2, 900)

    assert r1.DateEnd() == 900
    assert r1.DateBegin() == 900 + 1 - length      # DateEnd is derived


def test_dateend_column_reverts_bad_input(loaded_window):
    r1 = loaded_window.stack.base['s']['R1']
    good_end = r1.DateEnd()

    set_cell(loaded_window, 0, 2, 'xxxx')

    assert r1.DateEnd() == good_end
    assert loaded_window.ui.tableWidget_meas.item(0, 2).text() == str(good_end)


def test_sapwood_column_updates_meta(loaded_window):
    set_cell(loaded_window, 0, 4, 17)
    assert loaded_window.stack.base['s']['R1'].SapWood() == 17


def test_bark_column_updates_meta(loaded_window):
    set_cell(loaded_window, 0, 5, 'wk')
    assert loaded_window.stack.base['s']['R1'].export_meta('Bark') == 'wk'


def test_editing_redraws_chart(loaded_window, mocker):
    redraw = mocker.spy(type(loaded_window), 'redraw_chart')
    set_cell(loaded_window, 0, 5, 'wk')          # a column that doesn't revert
    assert redraw.called


# --- continue_sequence guards ------------------------------------

def test_continue_needs_exactly_one_selection(loaded_window, mocker):
    box = mocker.patch.object(QMessageBox, "setText")

    loaded_window.continue_sequence()            # nothing selected

    assert loaded_window.opened is False
    assert 'one sample' in box.call_args[0][0].lower()


def test_continue_warns_when_sample_missing_from_db(loaded_window, select_rows,
                                                    mocker):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    del loaded_window.stack.base['s']['R1']      # row still shown, key gone
    box = mocker.patch.object(QMessageBox, "setText")

    loaded_window.continue_sequence()

    assert loaded_window.opened is False
    assert 'not in the database' in box.call_args[0][0].lower()


# --- crossdate failure path -------------------------------------

def test_crossdate_failure_is_reported_not_raised(loaded_window, select_rows,
                                                  no_modals, mocker):
    select_rows(loaded_window.ui.tableWidget_meas, 0, 1, 2)
    mocker.patch.object(classes, 'crossdate_pairs',
                        side_effect=ValueError("boom"))
    box = mocker.patch.object(QMessageBox, "setText")

    loaded_window.correlate_sequences()          # must not propagate

    assert 'could not run' in box.call_args[0][0].lower()
