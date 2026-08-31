"""Sanity checks for the GUI test fixtures themselves."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox


def test_main_window_builds_with_fake_counter(main_window, fake_counter):
    assert main_window.dev is fake_counter
    assert main_window.testrun is False
    assert main_window.isVisible()


def test_fake_counter_scripts_reads(fake_counter):
    fake_counter.feed(120, 0, 135)
    assert fake_counter.read_measurement() == 120
    assert fake_counter.read_measurement() == 0
    assert fake_counter.read_measurement() == 135
    assert fake_counter.read_measurement() == 0      # exhausted -> no movement
    assert fake_counter.reads == 4


def test_no_modals_makes_message_box_nonblocking(no_modals, qapp):
    box = QMessageBox()
    assert box.exec() == QMessageBox.StandardButton.Ok       # would hang without


def test_no_modals_question_answer_is_steerable(no_modals, qapp):
    assert QMessageBox.question(None, "t", "?") == QMessageBox.StandardButton.Yes
    no_modals.question_answer = QMessageBox.StandardButton.No
    assert QMessageBox.question(None, "t", "?") == QMessageBox.StandardButton.No


def test_loaded_window_has_three_samples(loaded_window):
    assert loaded_window.order == ['R1', 'R2', 'R3']
    assert loaded_window.ui.tableWidget_meas.rowCount() == 3


def test_select_rows_helper(loaded_window, select_rows):
    select_rows(loaded_window.ui.tableWidget_meas, 0, 2)
    count, rows = loaded_window.selected_twmeas_rows()
    assert rows == [0, 2]
