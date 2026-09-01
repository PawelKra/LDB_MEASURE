"""End-to-end tests that drive the main window the way a user does: by
clicking the toolbar buttons and letting the wired-up slots run.

Every counter interaction goes through the scripted :class:`FakeCounter`
(``main_window`` fixture), and every modal is auto-answered (``no_modals``),
so a click that would normally pop a dialog just proceeds.
"""
import os

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

import classes


def click(qtbot, button):
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)


def name_cell(win, keycode):
    win.ui.tableWidget_attr.setItem(0, 0, QTableWidgetItem(keycode))


# --- sample lifecycle -------------------------------------------------

def test_click_new_sample_resets_everything(loaded_window, qtbot, no_modals):
    no_modals.question_answer = QMessageBox.StandardButton.No   # don't save
    assert loaded_window.order == ['R1', 'R2', 'R3']

    click(qtbot, loaded_window.ui.pushButton_new_sample)

    assert loaded_window.order == []
    assert loaded_window.ui.tableWidget_meas.rowCount() == 0
    assert loaded_window.saved is True


def test_click_load_sample_uses_file_dialog(main_window, qtbot, no_modals):
    no_modals.open_files = ['dane_test/deska1_3.fh',
                            'dane_test/STAR42.AVR',
                            'dane_test/STAR5.AVR']

    click(qtbot, main_window.ui.pushButton_load_sample)

    assert main_window.order == ['R1', 'R2', 'R3']
    assert main_window.ui.tableWidget_meas.rowCount() == 3
    assert main_window.saved is False


def test_click_save_sample_writes_files(main_window, qtbot, tmp_path, no_modals):
    no_modals.open_files = ['dane_test/deska1_3.fh']
    click(qtbot, main_window.ui.pushButton_load_sample)

    main_window.ui.lineEdit_cat_samples.setText(str(tmp_path))
    main_window.ui.lineEdit_cat_means.setText(str(tmp_path))
    name_cell(main_window, 'clicksave')

    click(qtbot, main_window.ui.pushButton_save_sample)

    assert main_window.saved is True
    assert os.path.exists(tmp_path / 'clicksave_R.fh')


def test_click_settings_opens_dialog(main_window, qtbot, mocker):
    import LDB_Measure
    import sett_window
    spy = mocker.patch.object(LDB_Measure, 'SettWindow',
                              wraps=sett_window.SettWindow)

    click(qtbot, main_window.ui.pushButton_settings)

    assert spy.called


def test_click_choose_dir_sets_paths(main_window, qtbot, tmp_path, no_modals):
    no_modals.directory = str(tmp_path)
    no_modals.question_answer = QMessageBox.StandardButton.Yes  # make R subdir

    click(qtbot, main_window.ui.pushButton_choose_dir)

    assert main_window.ui.lineEdit_cat_means.text() == str(tmp_path)
    assert main_window.ui.lineEdit_cat_samples.text() == str(tmp_path / 'R')
    assert (tmp_path / 'R').is_dir()


# --- measuring sequence lifecycle -----------------------------------

def test_click_new_sequence_opens_session_and_zeros_counter(
        main_window, qtbot, fake_counter, chart_lines):
    click(qtbot, main_window.ui.pushButton_new_sequence)

    assert main_window.opened.KeyCode() == 'R1'
    assert main_window.order == ['R1']
    assert fake_counter.zeroed >= 1            # setup_device zeroed it

    # an empty sequence draws nothing; the curve + cursor line appear once
    # the first increment lands
    fake_counter.feed(140)
    click(qtbot, main_window.ui.pushButton_read_measure)
    assert chart_lines(main_window) == 2


def test_full_measuring_session_by_clicks(
        main_window, qtbot, fake_counter, chart_lines):
    click(qtbot, main_window.ui.pushButton_new_sequence)

    # measure two rings, mark ring 2 as the first sapwood ring, measure three more
    fake_counter.feed(120, 135)
    for _ in range(2):
        click(qtbot, main_window.ui.pushButton_read_measure)

    click(qtbot, main_window.ui.pushButton_sapwood_beg)   # ring 2 = first sapwood
    assert main_window.ui.lineEdit_sapwood.text() == '2'

    fake_counter.feed(128, 140, 150)
    for _ in range(3):
        click(qtbot, main_window.ui.pushButton_read_measure)

    click(qtbot, main_window.ui.pushButton_end_measures)
    assert main_window.opened is False
    assert main_window.stack['s']['R1'].measurements() == [120, 135, 128, 140, 150]
    # rings 2,3,4,5 are sapwood -> a count of 4
    assert main_window.stack['s']['R1'].SapWood() == 4
    # chart shows the finished curve (+ the cursor axvline)
    assert chart_lines(main_window) == 2


def test_read_measure_ignored_when_no_movement(
        main_window, qtbot, fake_counter):
    click(qtbot, main_window.ui.pushButton_new_sequence)

    fake_counter.feed(0, 0)                     # encoder didn't move
    click(qtbot, main_window.ui.pushButton_read_measure)
    click(qtbot, main_window.ui.pushButton_read_measure)

    assert main_window.opened.measurements() == []


def test_read_measure_without_session_is_noop(main_window, qtbot, fake_counter):
    fake_counter.feed(150)
    click(qtbot, main_window.ui.pushButton_read_measure)   # no open sequence

    assert fake_counter.reads == 0             # should_be_opened blocked it


def test_click_clean_wipes_current_measures(
        main_window, qtbot, fake_counter):
    click(qtbot, main_window.ui.pushButton_new_sequence)
    fake_counter.feed(100, 110, 120)
    for _ in range(3):
        click(qtbot, main_window.ui.pushButton_read_measure)
    assert len(main_window.opened.measurements()) == 3

    zeroed_before = fake_counter.zeroed
    click(qtbot, main_window.ui.pushButton_clean)

    assert main_window.opened.measurements() == []
    assert fake_counter.zeroed == zeroed_before + 1


def test_click_delete_last_measure(main_window, qtbot, fake_counter):
    click(qtbot, main_window.ui.pushButton_new_sequence)
    fake_counter.feed(100, 110, 120)
    for _ in range(3):
        click(qtbot, main_window.ui.pushButton_read_measure)

    click(qtbot, main_window.ui.pushButton_delete_measure)

    assert main_window.opened.measurements() == [100, 110]


def test_click_continue_sequence(loaded_window, qtbot, select_rows):
    select_rows(loaded_window.ui.tableWidget_meas, 1)

    click(qtbot, loaded_window.ui.pushButton_continue_sequence)

    assert loaded_window.opened.KeyCode() == 'R2'


def test_click_delete_sequence(loaded_window, qtbot, select_rows, chart_lines):
    select_rows(loaded_window.ui.tableWidget_meas, 1)

    click(qtbot, loaded_window.ui.pushButton_delete_sequence)

    assert loaded_window.order == ['R1', 'R3']
    assert loaded_window.ui.tableWidget_meas.rowCount() == 2
    assert chart_lines(loaded_window) == 3          # 2 curves + cursor line


# --- derived products ---------------------------------------------

def test_click_mean_from_selected(loaded_window, qtbot, select_rows,
                                  chart_lines):
    select_rows(loaded_window.ui.tableWidget_meas, 0, 1, 2)

    click(qtbot, loaded_window.ui.pushButton_mean_selected)

    assert 'M1' in loaded_window.order
    assert loaded_window.ui.tableWidget_meas.rowCount() == 4
    assert loaded_window.stack['s']['M1'].Length() > 0
    assert chart_lines(loaded_window) == 5          # 4 curves + cursor line


def test_click_crossdate_selected_runs_crossdating(
        main_window, qtbot, select_rows, no_modals, mocker):
    no_modals.open_files = ['dane_test/proba_a.fh',
                            'dane_test/proba_b.fh',
                            'dane_test/deska1_3.fh']
    click(qtbot, main_window.ui.pushButton_load_sample)
    select_rows(main_window.ui.tableWidget_meas, 0, 1, 2)

    spy = mocker.spy(classes, 'crossdate_pairs')
    click(qtbot, main_window.ui.pushButton_cor_selected)

    assert spy.call_count == 1
    assert main_window.ui.tableWidget_meas.rowCount() == 3   # nothing lost


# --- clicking anything on an empty window must not abort -------------

# every toolbar button wired up in LDB_Measure.__init__
_ALL_BUTTONS = [
    "pushButton_new_sample", "pushButton_load_sample", "pushButton_save_sample",
    "pushButton_choose_dir", "pushButton_settings", "pushButton_new_sequence",
    "pushButton_continue_sequence", "pushButton_delete_sequence",
    "pushButton_cor_selected", "pushButton_mean_selected",
    "pushButton_read_measure", "pushButton_sapwood_beg",
    "pushButton_delete_measure", "pushButton_end_measures", "pushButton_clean",
]


@pytest.mark.parametrize("btn", _ALL_BUTTONS)
def test_button_on_fresh_window_does_not_crash(main_window, qtbot, no_modals,
                                               btn):
    # nothing loaded, no measuring session, no selection
    click(qtbot, getattr(main_window.ui, btn))
    assert main_window.isVisible()


def test_mean_from_selected_needs_at_least_two(loaded_window, qtbot,
                                               select_rows):
    # no selection -> message, no crash, no mean produced
    click(qtbot, loaded_window.ui.pushButton_mean_selected)
    assert not any(n.startswith('M') for n in loaded_window.order)

    # one selection -> still refused
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    click(qtbot, loaded_window.ui.pushButton_mean_selected)
    assert not any(n.startswith('M') for n in loaded_window.order)


def test_delete_last_measure_on_empty_open_sequence_is_safe(
        main_window, qtbot, fake_counter):
    click(qtbot, main_window.ui.pushButton_new_sequence)   # session open, 0 rings
    assert main_window.opened.measurements() == []

    click(qtbot, main_window.ui.pushButton_delete_measure)

    assert main_window.opened.measurements() == []          # no IndexError


# --- table <-> chart wiring -------------------------------------

def test_selecting_one_row_draws_stats_box(loaded_window, select_rows):
    texts_before = len(loaded_window.ui.widget.canvas.ax.texts)

    select_rows(loaded_window.ui.tableWidget_meas, 0)   # fires itemSelectionChanged

    # the per-sample name labels plus the correlation stats box
    assert len(loaded_window.ui.widget.canvas.ax.texts) > texts_before


def test_editing_datebegin_cell_syncs_db_and_chart(loaded_window):
    tw = loaded_window.ui.tableWidget_meas
    xlim_before = loaded_window.ui.widget.canvas.ax.get_xlim()

    tw.setItem(0, 1, QTableWidgetItem('750'))
    tw.cellChanged.emit(0, 1)

    assert loaded_window.stack.base['s']['R1'].DateBegin() == 750
    assert loaded_window.ui.widget.canvas.ax.get_xlim() != xlim_before
