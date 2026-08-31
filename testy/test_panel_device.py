"""``PanelDevice`` - the device-panel side: ``setup_device`` gatekeeping and
the "clean the panel" helpers.
"""
import pytest
from PyQt6.QtWidgets import QMessageBox


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
    from PyQt6.QtCore import Qt
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


def test_end_sequence_clears_the_device_panel(main_window, qtbot, fake_counter):
    from PyQt6.QtCore import Qt
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
