"""``editWindow`` - the standalone ring-editor dialog. Not wired into the
running app, but ported to PyQt6 and to the current ``classes.Sequence`` API,
so it builds and its editing operations work.
"""
import pytest
from PyQt6.QtWidgets import QWidget

import classes


@pytest.fixture
def editor(qtbot, no_modals):
    """An ``edycja_proby`` dialog over a 12-ring sample."""
    from editWindow import edycja_proby
    seq = classes.Sequence({'KeyCode': 'X', 'DateBegin': 100,
                            'measurements': [10, 11, 12, 13, 14, 15,
                                             16, 17, 18, 19, 20, 21]})
    dlg = edycja_proby(seq)
    qtbot.addWidget(dlg)
    return dlg


def test_module_imports():
    import editWindow
    assert hasattr(editWindow, "edycja_proby")
    assert hasattr(editWindow, "okno_podzialu")


def test_okno_podzialu_slider_bounds(qtbot):
    from editWindow import okno_podzialu

    dlg = okno_podzialu(value=50)
    qtbot.addWidget(dlg)

    assert dlg.s.minimum() == 1
    assert dlg.s.maximum() == 50


def test_okno_podzialu_split_updates_labels(qtbot):
    from editWindow import okno_podzialu

    dlg = okno_podzialu(value=50)
    qtbot.addWidget(dlg)

    dlg.s.setValue(20)                 # fires valueChanged -> uaktualnij()

    assert dlg.wart1.text() == "20"
    assert dlg.wart2.text() == "30"


def test_okno_podzialu_accept_records_both_halves(qtbot):
    from editWindow import okno_podzialu

    dlg = okno_podzialu(value=50)
    qtbot.addWidget(dlg)
    dlg.s.setValue(18)

    dlg.akceptuj()

    assert (dlg.val0, dlg.val1) == (18, 32)
    assert dlg.isHidden()


def test_qt4mplcanvas_builds_with_axes(qtbot):
    from editWindow import Qt4MplCanvas

    parent = QWidget()
    qtbot.addWidget(parent)
    canvas = Qt4MplCanvas(parent)

    assert canvas.axes is not None
    canvas.axes.plot([0, 1, 2], [2, 0, 1])
    canvas.draw()


def test_edycja_proby_builds_over_a_modern_sequence(editor):
    assert editor.newName == 'X'
    assert editor.sample.measurements() == [10, 11, 12, 13, 14, 15,
                                            16, 17, 18, 19, 20, 21]
    # 12 rings -> a 2-row 10-column grid
    assert editor.p_dane.rowCount() == 2
    assert len(editor.qmc.axes.lines) >= 1        # the sample curve is drawn


def test_editor_header_table_shows_metadata(editor):
    labels = [editor.p_naglowek.verticalHeaderItem(i).text()
              for i in range(editor.p_naglowek.rowCount())]
    assert 'KeyCode' in labels and 'DateBegin' in labels
    kc_row = labels.index('KeyCode')
    assert editor.p_naglowek.item(kc_row, 0).text() == 'X'


def test_editor_add_ring_at_selected_cell(editor, no_modals):
    no_modals.text_value = '999'
    editor.p_dane.item(0, 0).setSelected(True)

    editor.dodaj_wartosc()

    assert editor.sample.measurements()[0] == 999
    assert editor.sample.Length() == 13


def test_editor_delete_selected_ring(editor):
    editor.selected = [0]

    editor.usun_wartosc()

    assert editor.sample.measurements()[0] == 11        # the 10 is gone
    assert editor.sample.Length() == 11


def test_editor_divide_splits_a_ring(editor, no_modals, mocker):
    class FakeSplit:
        def __init__(self, value=0, parent=None):
            self.val0, self.val1 = 4, value - 4

        def exec(self):
            return 0

    mocker.patch('editWindow.okno_podzialu', FakeSplit)
    editor.selected = [0]

    editor.podziel_wartosc()

    assert editor.sample.measurements()[:2] == [4, 6]      # 10 -> 4 + 6
    assert editor.sample.Length() == 13
