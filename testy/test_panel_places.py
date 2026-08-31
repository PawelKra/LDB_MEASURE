"""``PanelPlaces.choose_dir`` - picking the working directory and whether to
carve out an ``R`` sub-folder for raw series.
"""
import pytest
from PyQt6.QtWidgets import QMessageBox


def test_choose_dir_aborts_on_empty_pick(main_window, no_modals):
    before = main_window.ui.lineEdit_cat_means.text()
    no_modals.directory = ''                      # user cancelled the dialog

    main_window.choose_dir()

    assert main_window.ui.lineEdit_cat_means.text() == before


def test_choose_dir_makes_R_subfolder_when_confirmed(main_window, no_modals,
                                                     tmp_path):
    no_modals.directory = str(tmp_path)
    no_modals.question_answer = QMessageBox.StandardButton.Yes

    main_window.choose_dir()

    assert main_window.ui.lineEdit_cat_means.text() == str(tmp_path)
    assert main_window.ui.lineEdit_cat_samples.text() == str(tmp_path / 'R')
    assert (tmp_path / 'R').is_dir()


def test_choose_dir_uses_same_folder_when_declined(main_window, no_modals,
                                                   tmp_path):
    no_modals.directory = str(tmp_path)
    no_modals.question_answer = QMessageBox.StandardButton.No

    main_window.choose_dir()

    assert main_window.ui.lineEdit_cat_samples.text() == str(tmp_path)
    assert not (tmp_path / 'R').exists()
