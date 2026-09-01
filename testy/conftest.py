"""Shared test fixtures.

Many tests reference data files by repo-root-relative paths
(``dane_test/proba_a.fh`` ...), so the whole session runs with the working
directory pinned to the repository root regardless of where pytest is invoked.

The GUI fixtures (``fake_counter``, ``main_window``, ``loaded_window``) let the
Qt tests drive a full measuring session without hardware and without any modal
dialog blocking the run - see ``no_modals``.
"""
import os
import pathlib

import pytest

# A test suite has no display: render Qt off-screen unless the caller already
# picked a platform. Must be set before QApplication is created (pytest-qt's
# ``qapp`` fixture), i.e. before any test imports PyQt6.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _run_from_repo_root():
    old = os.getcwd()
    os.chdir(REPO_ROOT)
    try:
        yield
    finally:
        os.chdir(old)


@pytest.fixture(autouse=True)
def _isolated_user_config(tmp_path_factory):
    """Point respath.user_config_dir() at a fresh throwaway dir for every test
    so the suite never touches the developer's real settings.txt
    (~/Library/Application Support/LDB_Measure, %APPDATA%\\LDB_Measure) and no
    test inherits another test's saved config."""
    cfg = tmp_path_factory.mktemp("ldb_config")
    old = os.environ.get("LDB_MEASURE_CONFIG_DIR")
    os.environ["LDB_MEASURE_CONFIG_DIR"] = str(cfg)
    try:
        yield cfg
    finally:
        if old is None:
            os.environ.pop("LDB_MEASURE_CONFIG_DIR", None)
        else:
            os.environ["LDB_MEASURE_CONFIG_DIR"] = old


@pytest.fixture
def data_dir():
    """Path to ``testy/data`` (golden JSON, multi.rwl, MIL fixtures)."""
    return pathlib.Path(__file__).resolve().parent / "data"


# --------------------------------------------------------------------------
# a scriptable stand-in for devices.Device (the measuring counter)
# --------------------------------------------------------------------------

class FakeCounter:
    """Drop-in replacement for :class:`devices.Device`.

    Feed it the increments a user would produce by turning the encoder
    (units of 1/100 mm, exactly what ``Device.read_measurement`` returns) and
    every ``read_measurement()`` call pops the next one. An empty script
    returns ``0`` - the app treats that as "no movement" and records nothing.
    """

    def __init__(self, readings=None):
        self.status = 1          # 1 == "counter present and reachable"
        self.opened = 0
        self.reading = 0
        self.readingA = 0
        self.readingB = 0
        self._script = list(readings or [])
        self.zeroed = 0          # how many times set_zeros() was called
        self.closed = 0          # how many times zamknij() was called
        self.reads = 0           # how many times read_measurement() was called

    def feed(self, *values):
        """Queue more increments for subsequent read_measurement() calls."""
        self._script.extend(values)

    def read_measurement(self):
        self.reads += 1
        self.reading = self._script.pop(0) if self._script else 0
        return self.reading

    def set_zeros(self):
        self.zeroed += 1
        self.readingA = self.readingB = 0

    def zamknij(self):
        self.closed += 1
        self.opened = 0


@pytest.fixture
def fake_counter():
    """A fresh, empty :class:`FakeCounter`; call ``.feed(...)`` to script it."""
    return FakeCounter()


# --------------------------------------------------------------------------
# stop every modal dialog from blocking a head-less run
# --------------------------------------------------------------------------

@pytest.fixture
def no_modals(monkeypatch):
    """Neutralise every blocking dialog the panels can raise.

    Returns a small config object so a test can steer the answers:

        no_modals.question_answer = QMessageBox.StandardButton.No
        no_modals.input_ok = False          # simulate the user hitting Cancel
        no_modals.open_files = ['a.fh']     # what getOpenFileNames returns
    """
    from PyQt6.QtWidgets import (QMessageBox, QInputDialog, QFileDialog,
                                 QDialog, QMenu)

    class Cfg:
        question_answer = QMessageBox.StandardButton.Yes
        input_ok = True             # False simulates the user hitting Cancel
        int_value = None            # None -> echo the dialog's default value
        text_value = None           # None -> echo the dialog's ``text`` kwarg
        open_files = []
        save_file = ""
        directory = ""

    cfg = Cfg()

    # QMessageBox - instance .exec() and the static helpers
    monkeypatch.setattr(QMessageBox, "exec",
                        lambda self, *a, **k: QMessageBox.StandardButton.Ok,
                        raising=False)
    monkeypatch.setattr(QMessageBox, "question",
                        staticmethod(lambda *a, **k: cfg.question_answer))
    for _name in ("information", "warning", "critical", "about"):
        monkeypatch.setattr(QMessageBox, _name,
                            staticmethod(
                                lambda *a, **k: QMessageBox.StandardButton.Ok))

    # QInputDialog - echo back the supplied default so add/change slots have a
    # sensible value to work with
    def _get_int(parent, title, label, value=0, *a, **k):
        out = value if cfg.int_value is None else cfg.int_value
        return (out, cfg.input_ok)

    def _get_text(parent, title, label, *a, **k):
        out = k.get("text", "") if cfg.text_value is None else cfg.text_value
        return (out, cfg.input_ok)

    def _get_double(parent, title, label, value=0.0, *a, **k):
        return (value, cfg.input_ok)

    monkeypatch.setattr(QInputDialog, "getInt", staticmethod(_get_int))
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(_get_text))
    monkeypatch.setattr(QInputDialog, "getDouble", staticmethod(_get_double))

    # QFileDialog - every getter, static or bound
    monkeypatch.setattr(QFileDialog, "getOpenFileNames",
                        staticmethod(lambda *a, **k: (list(cfg.open_files), "")))
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (
                            cfg.open_files[0] if cfg.open_files else "", "")))
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (cfg.save_file, "")))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory",
                        staticmethod(lambda *a, **k: cfg.directory))

    # any sub-dialog opened with .exec() (SettWindow, Results, Options)
    monkeypatch.setattr(QDialog, "exec",
                        lambda self, *a, **k: QDialog.DialogCode.Rejected,
                        raising=False)
    # context menus pop up non-modally, but never actually show one in a test
    monkeypatch.setattr(QMenu, "popup", lambda self, *a, **k: None)
    monkeypatch.setattr(QMenu, "exec", lambda self, *a, **k: None,
                        raising=False)

    return cfg


# --------------------------------------------------------------------------
# the main window, wired for GUI tests
# --------------------------------------------------------------------------

@pytest.fixture
def main_window(qtbot, fake_counter, no_modals):
    """A live ``LDB_Form`` with the counter replaced by ``fake_counter``.

    ``testrun`` is deliberately left False so the real device code path
    (``setup_device`` -> ``dev.status`` / ``dev.set_zeros``) is exercised
    against the fake.
    """
    import LDB_Measure

    win = LDB_Measure.LDB_Form()
    win.dev = fake_counter
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)
    return win


@pytest.fixture
def loaded_window(main_window):
    """``main_window`` with three real samples already loaded (R1, R2, R3)."""
    main_window.test_samples = ['dane_test/deska1_3.fh',
                                'dane_test/STAR42.AVR',
                                'dane_test/STAR5.AVR']
    main_window.load_samples()
    main_window.test_samples = []
    return main_window


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

class MplEvent:
    """The handful of matplotlib MouseEvent attributes the chart slots read."""

    def __init__(self, button=1, xdata=0.0, ydata=0.0, inaxes=True):
        self.button = button
        self.xdata = xdata
        self.ydata = ydata
        self.inaxes = inaxes


@pytest.fixture
def mpl_event():
    return MplEvent


@pytest.fixture
def select_rows():
    """select_rows(table, 0, 2) -> select whole rows 0 and 2 in a QTableWidget."""
    from PyQt6.QtWidgets import QTableWidgetSelectionRange

    def _select(table, *rows):
        table.clearSelection()
        last_col = table.columnCount() - 1
        for r in rows:
            table.setRangeSelected(
                QTableWidgetSelectionRange(r, 0, r, last_col), True)
    return _select


@pytest.fixture
def chart_lines():
    """chart_lines(win) -> number of Line2D artists on the main chart."""
    def _count(win):
        return len(win.ui.widget.canvas.ax.lines)
    return _count
