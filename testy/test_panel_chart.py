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


def _sapwood_line(win):
    return next(l for l in win.ui.widget.canvas.ax.lines
                if l.get_color() == 'gray' and l.get_linewidth() == 4)


def test_sapwood_bold_covers_exactly_the_last_N_rings(loaded_window):
    r1 = loaded_window.stack.base['s']['R1']
    r1.set_meta('SapWood', 4)
    loaded_window.redraw_chart()

    xs = list(_sapwood_line(loaded_window).get_xdata())
    ys = list(_sapwood_line(loaded_window).get_ydata())
    assert xs == list(range(r1.DateEnd() - 3, r1.DateEnd() + 1))   # 4 years
    assert all(y > 0 for y in ys)                    # no measure_from_year False->0


def test_sapwood_bold_is_clamped_to_the_curve(loaded_window):
    r1 = loaded_window.stack.base['s']['R1']
    r1.set_meta('SapWood', r1.Length() + 50)          # absurd count
    loaded_window.redraw_chart()

    xs = list(_sapwood_line(loaded_window).get_xdata())
    assert min(xs) == r1.DateBegin()                  # never before the curve
    assert max(xs) == r1.DateEnd()
    assert all(y > 0 for y in _sapwood_line(loaded_window).get_ydata())


def test_stats_box_only_with_one_selection_and_more_than_one_sample(
        loaded_window, select_rows):
    ax = loaded_window.ui.widget.canvas.ax

    select_rows(loaded_window.ui.tableWidget_meas, 0, 1)      # two rows
    two_sel = len(ax.texts)

    select_rows(loaded_window.ui.tableWidget_meas, 0)         # one row
    one_sel = len(ax.texts)

    assert one_sel > two_sel      # the KEY/CC/TBP... box is drawn only for one


# --- right-click context menu --------------------------------------

def _menu_labels(win):
    return [a.text() for a in win.menu.actions() if not a.isSeparator()]


def _menu_action(win, text):
    return next(a for a in win.menu.actions() if a.text() == text)


def test_right_click_with_one_row_offers_edit_actions(
        loaded_window, select_rows, mpl_event):
    select_rows(loaded_window.ui.tableWidget_meas, 1)

    loaded_window.mouseClick(mpl_event(button=3, xdata=180))

    assert _menu_labels(loaded_window)[:3] == ['Delete', 'Add', 'Modify']


def test_right_click_with_no_selection_shows_reminder(loaded_window, mpl_event):
    loaded_window.mouseClick(mpl_event(button=3, xdata=180))

    labels = _menu_labels(loaded_window)
    assert 'only one sample' in labels[0]
    # undo / redo are still offered, just disabled with no history
    assert labels[1:] == ['Undo ring edit', 'Redo ring edit']


def test_undo_redo_actions_disabled_until_there_is_history(
        loaded_window, select_rows, mpl_event):
    select_rows(loaded_window.ui.tableWidget_meas, 0)

    loaded_window.mouseClick(mpl_event(button=3, xdata=180))
    assert _menu_action(loaded_window, 'Undo ring edit').isEnabled() is False
    assert _menu_action(loaded_window, 'Redo ring edit').isEnabled() is False

    loaded_window.delete_slot(mpl_event(xdata=180))

    loaded_window.mouseClick(mpl_event(button=3, xdata=180))
    assert _menu_action(loaded_window, 'Undo ring edit').isEnabled() is True
    assert _menu_action(loaded_window, 'Redo ring edit').isEnabled() is False

    loaded_window.undo_edit()

    loaded_window.mouseClick(mpl_event(button=3, xdata=180))
    assert _menu_action(loaded_window, 'Undo ring edit').isEnabled() is False
    assert _menu_action(loaded_window, 'Redo ring edit').isEnabled() is True


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


# --- undo / redo of ring edits ---------------------------------------

def test_undo_reverts_a_ring_delete(loaded_window, select_rows, mpl_event):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']
    before = list(r1.measurements())

    loaded_window.delete_slot(mpl_event(xdata=180))
    assert list(r1.measurements()) != before

    loaded_window.undo_edit()
    assert list(r1.measurements()) == before
    assert loaded_window.saved is False


def test_redo_reapplies_an_undone_edit(loaded_window, select_rows, mpl_event):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']

    loaded_window.delete_slot(mpl_event(xdata=180))
    after_delete = list(r1.measurements())

    loaded_window.undo_edit()
    loaded_window.redo_edit()
    assert list(r1.measurements()) == after_delete


def test_undo_then_new_edit_clears_redo(loaded_window, select_rows, mpl_event,
                                        no_modals):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']

    loaded_window.delete_slot(mpl_event(xdata=180))
    loaded_window.undo_edit()
    assert loaded_window._redo_stack                      # redo available

    no_modals.int_value = 999
    loaded_window.change_slot(mpl_event(xdata=181))
    assert loaded_window._redo_stack == []                # a new edit drops it

    n_undo = len(loaded_window._undo_stack)
    loaded_window.redo_edit()                             # nothing to redo
    assert len(loaded_window._undo_stack) == n_undo
    assert r1.measure_from_year(181) == 999


def test_undo_walks_back_several_edits_across_samples(loaded_window,
                                                     select_rows, mpl_event):
    r1 = loaded_window.stack.base['s']['R1']
    r2 = loaded_window.stack.base['s']['R2']
    r1_before, r2_before = list(r1.measurements()), list(r2.measurements())

    select_rows(loaded_window.ui.tableWidget_meas, 0)
    loaded_window.delete_slot(mpl_event(xdata=180))
    select_rows(loaded_window.ui.tableWidget_meas, 1)
    loaded_window.delete_slot(mpl_event(xdata=r2.DateBegin() + 2))

    assert list(r1.measurements()) != r1_before
    assert list(r2.measurements()) != r2_before

    loaded_window.undo_edit()                        # undoes the R2 delete
    assert list(r2.measurements()) == r2_before
    assert list(r1.measurements()) != r1_before

    loaded_window.undo_edit()                        # undoes the R1 delete
    assert list(r1.measurements()) == r1_before


def test_undo_with_no_history_is_a_harmless_noop(loaded_window):
    loaded_window.undo_edit()
    loaded_window.redo_edit()
    assert 'undo' in loaded_window.ui.statusbar.currentMessage().lower() \
        or 'redo' in loaded_window.ui.statusbar.currentMessage().lower()


def test_new_sample_clears_the_undo_history(loaded_window, select_rows,
                                            mpl_event, no_modals):
    from PyQt6.QtWidgets import QMessageBox

    select_rows(loaded_window.ui.tableWidget_meas, 0)
    loaded_window.delete_slot(mpl_event(xdata=180))
    assert loaded_window._undo_stack

    no_modals.question_answer = QMessageBox.StandardButton.No   # discard
    loaded_window.new_sample()
    assert loaded_window._undo_stack == []
    assert loaded_window._redo_stack == []


def test_undo_stack_is_bounded(loaded_window, select_rows, mpl_event,
                               no_modals):
    select_rows(loaded_window.ui.tableWidget_meas, 0)
    r1 = loaded_window.stack.base['s']['R1']
    year = r1.DateBegin() + 1

    for i in range(loaded_window._UNDO_LIMIT + 10):
        no_modals.int_value = 100 + i
        loaded_window.change_slot(mpl_event(xdata=year))

    assert len(loaded_window._undo_stack) == loaded_window._UNDO_LIMIT
