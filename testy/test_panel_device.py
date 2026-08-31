"""``PanelDevice`` - the device-panel side: ``setup_device`` gatekeeping,
sapwood marking, and the "clean the panel" helpers.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox


def _measure(win, qtbot, fake_counter, *values):
    fake_counter.feed(*values)
    for _ in values:
        qtbot.mouseClick(win.ui.pushButton_read_measure, Qt.MouseButton.LeftButton)


def test_setup_device_zeros_a_present_counter(main_window, fake_counter):
    assert main_window.setup_device() is True
    assert fake_counter.zeroed == 1


def test_setup_device_refuses_when_counter_absent(main_window, fake_counter,
                                                  no_modals, mocker):
    fake_counter.status = 0
    box = mocker.patch.object(QMessageBox, "setText")

    assert main_window.setup_device() is False
    assert 'no device found' in box.call_args[0][0].lower()


def test_new_sequence_blocked_when_counter_absent(main_window, qtbot,
                                                  fake_counter, no_modals):
    fake_counter.status = 0

    qtbot.mouseClick(main_window.ui.pushButton_new_sequence,
                     Qt.MouseButton.LeftButton)

    assert main_window.opened is False
    assert main_window.order == []


def test_setup_device_skipped_entirely_in_testrun(main_window, fake_counter):
    main_window.testrun = True
    fake_counter.status = 0                 # would normally block

    assert main_window.setup_device() is True
    assert fake_counter.zeroed == 0         # not touched


def test_set_sapwood_marks_ring_and_end_stores_a_ring_count(
        main_window, qtbot, fake_counter):
    qtbot.mouseClick(main_window.ui.pushButton_new_sequence,
                     Qt.MouseButton.LeftButton)

    _measure(main_window, qtbot, fake_counter, 10, 11, 12, 13, 14, 15)
    qtbot.mouseClick(main_window.ui.pushButton_sapwood_beg,
                     Qt.MouseButton.LeftButton)          # ring 6 = first sapwood
    assert main_window.ui.lineEdit_sapwood.text() == '6'
    assert main_window.sapwood_beg == 6

    _measure(main_window, qtbot, fake_counter, 16, 17, 18, 19)   # -> 10 rings
    qtbot.mouseClick(main_window.ui.pushButton_end_measures,
                     Qt.MouseButton.LeftButton)

    # rings 6..10 are sapwood -> count 5
    assert main_window.stack['s']['R1'].SapWood() == 5
    assert main_window.sapwood_beg == 0                  # reset for next session


def test_sapwood_count_typed_directly_is_stored_as_is(
        main_window, qtbot, fake_counter):
    qtbot.mouseClick(main_window.ui.pushButton_new_sequence,
                     Qt.MouseButton.LeftButton)
    _measure(main_window, qtbot, fake_counter, 10, 11, 12, 13, 14)

    main_window.ui.lineEdit_sapwood.setText('3')         # no button -> a count
    qtbot.mouseClick(main_window.ui.pushButton_end_measures,
                     Qt.MouseButton.LeftButton)

    assert main_window.stack['s']['R1'].SapWood() == 3


def test_end_sequence_clears_the_device_panel(main_window, qtbot, fake_counter):
    qtbot.mouseClick(main_window.ui.pushButton_new_sequence,
                     Qt.MouseButton.LeftButton)
    fake_counter.feed(120, 130)
    for _ in range(2):
        qtbot.mouseClick(main_window.ui.pushButton_read_measure,
                         Qt.MouseButton.LeftButton)
    main_window.ui.lineEdit_sapwood.setText('2')

    qtbot.mouseClick(main_window.ui.pushButton_end_measures,
                     Qt.MouseButton.LeftButton)

    assert main_window.ui.textEdit_meas.toPlainText() == ''
    assert main_window.ui.lineEdit_sapwood.text() == ''
