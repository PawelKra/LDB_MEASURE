"""``UserDecorators`` - the guard decorators the panels hang off:

* ``should_be_closed``  - run only when no measuring session is open
* ``should_be_opened``  - run only when one is
* ``select_measure_button`` - after running, park focus on "Read measure"
"""
import pytest
from PyQt6.QtWidgets import QMessageBox

from user_decorators import UserDecorators


class Dummy:
    """Minimal stand-in for LDB_Form as far as the decorators care."""
    def __init__(self, opened):
        self.opened = opened
        self.ran = False

    @UserDecorators.should_be_closed
    def only_when_closed(self):
        self.ran = True

    @UserDecorators.should_be_opened
    def only_when_open(self):
        self.ran = True


def test_should_be_closed_runs_when_no_session(qapp):
    d = Dummy(opened=False)
    d.only_when_closed()
    assert d.ran is True


def test_should_be_closed_blocks_and_warns_during_session(qapp, no_modals,
                                                          mocker):
    set_text = mocker.patch.object(QMessageBox, "setText")
    d = Dummy(opened=object())          # a live session

    d.only_when_closed()

    assert d.ran is False
    assert "end measuring session" in set_text.call_args[0][0].lower()


def test_should_be_opened_runs_during_session(qapp):
    d = Dummy(opened=object())
    d.only_when_open()
    assert d.ran is True


def test_should_be_opened_blocks_without_session(qapp, no_modals, mocker):
    set_text = mocker.patch.object(QMessageBox, "setText")
    d = Dummy(opened=False)

    d.only_when_open()

    assert d.ran is False
    assert "start new sequence" in set_text.call_args[0][0].lower()


def test_select_measure_button_parks_focus(main_window, qtbot):
    main_window.ui.pushButton_new_sample.setFocus()

    # new_sequence is wrapped with select_measure_button
    main_window.new_sequence()

    assert main_window.ui.pushButton_read_measure.hasFocus()
