"""``PanelSample`` - new / load / save of a whole sample, driven through the
window API with the file dialogs and confirmation boxes auto-answered.
"""
import os

import pytest
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

import classes


def name_cell(win, keycode):
    win.ui.tableWidget_attr.setItem(0, 0, QTableWidgetItem(keycode))


def load_one(win):
    win.test_samples = ['dane_test/deska1_3.fh']
    win.load_samples()
    win.test_samples = []


# --- new_sample -----------------------------------------------------

def test_new_sample_prompts_and_resets_when_declined(main_window, no_modals):
    load_one(main_window)
    assert main_window.saved is False
    no_modals.question_answer = QMessageBox.StandardButton.No

    main_window.new_sample()

    assert main_window.order == []
    assert main_window.saved is True


def test_new_sample_aborts_when_save_is_chosen_but_fails(main_window, no_modals):
    load_one(main_window)
    no_modals.question_answer = QMessageBox.StandardButton.Yes
    # no KeyCode set -> save_sample() bails -> new_sample bails too

    main_window.new_sample()

    assert main_window.order == ['R1']            # nothing was reset


def test_new_sample_with_save_accepted_writes_the_files(main_window, no_modals,
                                                        tmp_path):
    load_one(main_window)
    main_window.ui.lineEdit_cat_samples.setText(str(tmp_path))
    main_window.ui.lineEdit_cat_means.setText(str(tmp_path))
    name_cell(main_window, 'accepted')
    no_modals.question_answer = QMessageBox.StandardButton.Yes

    main_window.new_sample()

    assert (tmp_path / 'accepted_R.fh').exists()


def test_new_sample_resets_after_a_successful_save(main_window, no_modals,
                                                   tmp_path):
    load_one(main_window)
    main_window.ui.lineEdit_cat_samples.setText(str(tmp_path))
    main_window.ui.lineEdit_cat_means.setText(str(tmp_path))
    name_cell(main_window, 'accepted')
    no_modals.question_answer = QMessageBox.StandardButton.Yes

    main_window.new_sample()

    assert main_window.order == []


# --- save_sample ---------------------------------------------------

def test_save_requires_a_keycode(main_window, no_modals, mocker):
    load_one(main_window)
    set_text = mocker.patch.object(QMessageBox, "setText")

    main_window.save_sample()

    assert 'keycode' in set_text.call_args[0][0].lower()
    assert main_window.saved is False                 # nothing was written


@pytest.mark.parametrize("combo_index, produced", [
    (0, ['s_R.fh']),                        # *.fh  - one multi-series file
    (1, ['s_R1.txt']),                      # *.txt - one file per series
    (2, ['s_R1.avr']),                      # *.avr - one file per series
])
def test_save_writes_each_supported_format(main_window, no_modals, tmp_path,
                                           combo_index, produced):
    load_one(main_window)
    main_window.ui.lineEdit_cat_samples.setText(str(tmp_path))
    main_window.ui.lineEdit_cat_means.setText(str(tmp_path))
    name_cell(main_window, 's')
    main_window.ui.comboBox_format.setCurrentIndex(combo_index)

    main_window.save_sample()

    assert main_window.saved is True
    for fname in produced:
        assert (tmp_path / fname).exists()


def test_save_overwrite_prompt_can_abort(main_window, no_modals, tmp_path):
    load_one(main_window)
    main_window.ui.lineEdit_cat_samples.setText(str(tmp_path))
    main_window.ui.lineEdit_cat_means.setText(str(tmp_path))
    name_cell(main_window, 'dup')

    main_window.save_sample()                         # first write
    assert main_window.saved is True
    stamp = (tmp_path / 'dup_R.fh').stat().st_mtime_ns

    main_window.saved = False
    no_modals.question_answer = QMessageBox.StandardButton.No
    main_window.save_sample()                         # refused to overwrite

    assert main_window.saved is False
    assert (tmp_path / 'dup_R.fh').stat().st_mtime_ns == stamp


# --- load_samples ------------------------------------------------

def test_load_via_dialog_populates_table(main_window, no_modals):
    no_modals.open_files = ['dane_test/deska1_3.fh',
                            'dane_test/STAR42.AVR']

    main_window.load_samples()

    assert main_window.order == ['R1', 'R2']
    assert main_window.ui.tableWidget_meas.rowCount() == 2


def test_load_skips_unsupported_extensions(main_window, no_modals):
    no_modals.open_files = ['dane_test/deska1_3.fh',
                            'dane_test/result.txt']       # not a sample format

    main_window.load_samples()

    assert main_window.order == ['R1']                     # the .txt was ignored


def test_load_refuses_more_than_twenty_samples(main_window, no_modals, mocker):
    many = {'x%02d' % i: classes.Sequence({'KeyCode': 'x%02d' % i,
                                           'measurements': [1, 2, 3]})
            for i in range(21)}
    mocker.patch.object(classes, 'read_fh', return_value=many)
    box = mocker.patch.object(QMessageBox, "setText")
    no_modals.open_files = ['dane_test/deska1_3.fh']

    main_window.load_samples()

    assert main_window.order == []
    assert 'only 20' in box.call_args[0][0].lower()
