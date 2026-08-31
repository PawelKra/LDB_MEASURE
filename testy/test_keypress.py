"""Keyboard shortcuts defined by ``PanelMeasurements.keyPressEvent``:

    Space  -> read one measurement from the counter
    F3/F4  -> nudge DateBegin of every selected sample down / up one year
    Up/Dn  -> change the on-chart drawing offset

``LDB_Form`` binds ``PanelMeasurements.keyPressEvent`` explicitly (it would
otherwise be shadowed by ``QWidget.keyPressEvent`` in the MRO), so the calls
below go through the window's own ``keyPressEvent``.
"""
import pytest
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QKeyEvent


def dispatch(win, key):
    ev = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
    win.keyPressEvent(ev)


def test_f3_shifts_selected_sample_one_year_earlier(loaded_window, select_rows):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    seq = loaded_window.stack.base['s'][loaded_window.order[0]]
    d0 = seq.DateBegin()

    dispatch(loaded_window, Qt.Key.Key_F3)

    assert seq.DateBegin() == d0 - 1
    assert loaded_window.ui.tableWidget_meas.item(0, 1).text() == str(d0 - 1)


def test_f4_shifts_selected_sample_one_year_later(loaded_window, select_rows):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    seq = loaded_window.stack.base['s'][loaded_window.order[0]]
    d0 = seq.DateBegin()

    dispatch(loaded_window, Qt.Key.Key_F4)

    assert seq.DateBegin() == d0 + 1


def test_f3_moves_every_selected_sample(loaded_window, select_rows):
    select_rows(loaded_window.ui.tableWidget_meas, 0, 2)
    a = loaded_window.stack.base['s'][loaded_window.order[0]]
    c = loaded_window.stack.base['s'][loaded_window.order[2]]
    da, dc = a.DateBegin(), c.DateBegin()

    dispatch(loaded_window, Qt.Key.Key_F3)

    assert (a.DateBegin(), c.DateBegin()) == (da - 1, dc - 1)


def test_arrow_up_and_down_change_offset(main_window):
    start = main_window.offset

    dispatch(main_window, Qt.Key.Key_Up)
    assert main_window.offset == start + 1

    dispatch(main_window, Qt.Key.Key_Down)
    dispatch(main_window, Qt.Key.Key_Down)
    assert main_window.offset == start - 1


def test_offset_never_goes_negative(main_window):
    main_window.offset = 0
    dispatch(main_window, Qt.Key.Key_Down)
    assert main_window.offset == 0


def test_space_reads_one_measurement(main_window, qtbot, fake_counter):
    qtbot.mouseClick(main_window.ui.pushButton_new_sequence,
                     Qt.MouseButton.LeftButton)
    fake_counter.feed(175)

    dispatch(main_window, Qt.Key.Key_Space)

    assert main_window.opened.measurements() == [175]


def test_space_without_session_records_nothing(main_window, fake_counter):
    fake_counter.feed(175)
    dispatch(main_window, Qt.Key.Key_Space)
    assert fake_counter.reads == 0


def test_keypressevent_is_wired_to_the_window(main_window):
    start = main_window.offset
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up,
                   Qt.KeyboardModifier.NoModifier)
    main_window.keyPressEvent(ev)          # the window's own dispatch
    assert main_window.offset == start + 1


# --- through real Qt key delivery (QTest.keyClick), not a hand-built event --

def test_space_activates_a_measurement_via_real_keypress(
        main_window, qtbot, fake_counter):
    from PyQt6.QtTest import QTest
    qtbot.mouseClick(main_window.ui.pushButton_new_sequence,
                     Qt.MouseButton.LeftButton)
    fake_counter.feed(182)

    main_window.setFocus()
    QTest.keyClick(main_window, Qt.Key.Key_Space)

    assert main_window.opened.measurements() == [182]


def test_f3_shifts_datebegin_via_real_keypress(loaded_window, qtbot,
                                               select_rows):
    from PyQt6.QtTest import QTest
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    seq = loaded_window.stack.base['s'][loaded_window.order[0]]
    d0 = seq.DateBegin()

    loaded_window.setFocus()
    QTest.keyClick(loaded_window, Qt.Key.Key_F3)

    assert seq.DateBegin() == d0 - 1
