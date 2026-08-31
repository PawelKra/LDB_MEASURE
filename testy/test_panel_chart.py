"""Chart panel: what ``redraw_chart`` puts on the canvas, the right-click
context menu, the cursor line follow, and the in-place edit slots.

All of these are wired to the matplotlib canvas events / a ``QMenu`` in the
running app; the tests call the same handlers with lightweight fake events
(``mpl_event`` fixture).
"""
import pytest
from PyQt6.QtCore import Qt


# --- redraw_chart -----------------------------------------------------

def test_empty_chart_is_just_the_cursor_line(main_window, chart_lines):
    # __init__ already called new_sample(); nothing loaded
    main_window.redraw_chart()
    assert chart_lines(main_window) == 1       # only the axvline cursor
    assert main_window.ui.widget.canvas.ax.get_xlim() == (0.0, 70.0)


def test_chart_bails_before_drawing_when_a_sample_has_no_rings(
        main_window, qtbot, fake_counter, chart_lines):
    qtbot.mouseClick(main_window.ui.pushButton_new_sequence,
                     Qt.MouseButton.LeftButton)
    # R1 exists but holds zero measurements -> redraw returns early
    assert chart_lines(main_window) == 0


def test_chart_draws_one_line_per_sample_plus_cursor(loaded_window,
                                                     chart_lines):
    loaded_window.redraw_chart()
    # 3 samples -> 3 curves + the axvline cursor
    assert chart_lines(loaded_window) == 4


def test_chart_labels_each_curve_with_its_keycode(loaded_window):
    loaded_window.redraw_chart()
    labels = {t.get_text() for t in loaded_window.ui.widget.canvas.ax.texts}
    assert {'R1', 'R2', 'R3'} <= labels


def test_chart_xlim_tracks_sample_dates(loaded_window):
    loaded_window.stack.base['s']['R1'].setDateBegin(1000)
    loaded_window.stack.base['s']['R2'].setDateBegin(1000)
    loaded_window.stack.base['s']['R3'].setDateBegin(1000)
    loaded_window.redraw_chart()

    lo, hi = loaded_window.ui.widget.canvas.ax.get_xlim()
    assert lo == 999                       # min DateBegin - 1
    assert hi > 1000


def test_sapwood_adds_a_second_line_for_that_sample(loaded_window,
                                                    chart_lines):
    before = chart_lines(loaded_window)
    loaded_window.stack.base['s']['R1'].set_meta('SapWood', 12)
    loaded_window.redraw_chart()
    assert chart_lines(loaded_window) == before + 1     # the gray sapwood trace


def test_stats_box_only_with_one_selection_and_more_than_one_sample(
        loaded_window, select_rows):
    ax = loaded_window.ui.widget.canvas.ax

    select_rows(loaded_window.ui.tableWidget_meas, 0, 1)      # two rows
    two_sel = len(ax.texts)

    select_rows(loaded_window.ui.tableWidget_meas, 0)         # one row
    one_sel = len(ax.texts)

    assert one_sel > two_sel      # the KEY/CC/TBP... box is drawn only for one


# --- right-click context menu --------------------------------------

def test_right_click_with_one_row_offers_edit_actions(
        loaded_window, select_rows, mpl_event):
    select_rows(loaded_window.ui.tableWidget_meas, 1)

    loaded_window.mouseClick(mpl_event(button=3, xdata=180))

    labels = [a.text() for a in loaded_window.menu.actions()]
    assert labels == ['Delete', 'Add', 'Modify']


def test_right_click_with_no_selection_shows_reminder(loaded_window, mpl_event):
    loaded_window.mouseClick(mpl_event(button=3, xdata=180))

    labels = [a.text() for a in loaded_window.menu.actions()]
    assert len(labels) == 1 and 'only one sample' in labels[0]


def test_left_click_on_chart_opens_no_menu(loaded_window, mpl_event):
    if hasattr(loaded_window, 'menu'):
        del loaded_window.menu
    loaded_window.mouseClick(mpl_event(button=1, xdata=180))
    assert not hasattr(loaded_window, 'menu')


# --- cursor line follows the mouse -------------------------------

def test_mouse_move_shifts_cursor_line(loaded_window, mpl_event):
    loaded_window.redraw_chart()

    loaded_window.onMouseMove(mpl_event(xdata=185.4))
    assert loaded_window.line_x == 185

    loaded_window.onMouseMove(mpl_event(xdata=210.9))
    assert loaded_window.line_x == 210
    assert list(loaded_window.line.get_xdata()) == [210.9, 210.9]


def test_mouse_move_outside_axes_is_ignored(loaded_window, mpl_event):
    loaded_window.redraw_chart()
    loaded_window.onMouseMove(mpl_event(xdata=150))
    assert loaded_window.line_x == 150

    loaded_window.onMouseMove(mpl_event(xdata=None))
    assert loaded_window.line_x == 150            # unchanged


# --- in-place edit slots (fired from the context menu) -----------

def test_delete_slot_removes_the_ring_at_that_year(
        loaded_window, select_rows, mpl_event):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']
    n0 = r1.Length()

    loaded_window.delete_slot(mpl_event(xdata=180))

    assert r1.Length() == n0 - 1
    assert loaded_window.saved is False


def test_add_slot_inserts_a_ring(loaded_window, select_rows, mpl_event,
                                 no_modals):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']
    n0 = r1.Length()

    loaded_window.add_slot(mpl_event(xdata=180))

    assert r1.Length() == n0 + 1
    assert loaded_window.saved is False


def test_add_slot_respects_cancel(loaded_window, select_rows, mpl_event,
                                  no_modals):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']
    n0 = r1.Length()
    no_modals.input_ok = False               # user hit Cancel

    loaded_window.add_slot(mpl_event(xdata=180))

    assert r1.Length() == n0


def test_change_slot_overwrites_the_ring_value(loaded_window, select_rows,
                                               mpl_event, no_modals):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']
    no_modals.int_value = 4242

    loaded_window.change_slot(mpl_event(xdata=180))

    assert r1.measure_from_year(180) == 4242


def test_edit_slots_need_exactly_one_selection(loaded_window, select_rows,
                                               mpl_event):
    select_rows(loaded_window.ui.tableWidget_meas, 0, 1)      # two selected
    r1 = loaded_window.stack.base['s']['R1']
    n0 = r1.Length()

    loaded_window.delete_slot(mpl_event(xdata=180))

    assert r1.Length() == n0                  # nothing happened
