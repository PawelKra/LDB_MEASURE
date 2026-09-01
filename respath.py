"""Filesystem paths that work the same from a source checkout and from a
frozen PyInstaller bundle.

Two kinds of path:

* **bundled, read-only** - icons, ``Monospace.ttf``. Shipped inside the app;
  ``resource_path()`` finds them under ``sys._MEIPASS`` when frozen, next to
  the sources otherwise.
* **per-user, writable** - ``settings.txt``. Never lives inside the bundle
  (that is read-only on macOS and thrown away on every launch for a one-file
  build). ``user_config_dir()`` puts it in the platform's app-data area, or
  wherever ``LDB_MEASURE_CONFIG_DIR`` points if that is set (portable mode /
  ops override / the test-suite).
"""
import os
import sys

APP_NAME = "LDB_Measure"
CONFIG_DIR_ENV = "LDB_MEASURE_CONFIG_DIR"


def resource_path(rel):
    """Absolute, native path to a read-only resource shipped with the app.

    ``rel`` is always given with ``/`` separators; normpath collapses those
    to ``os.sep`` so the result is a canonical path on Windows too (a bare
    ``os.path.join`` would leave ``base\\ikonki/UP.png``).
    """
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
        os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base, *rel.split("/")))


def user_config_dir():
    """Writable directory for the user's settings, created if missing.

    ``LDB_MEASURE_CONFIG_DIR`` wins when set. Otherwise Qt's
    ``AppDataLocation`` (``~/Library/Application Support/LDB_Measure``,
    ``%APPDATA%\\LDB_Measure``, ``~/.local/share/LDB_Measure``); if Qt is
    somehow unavailable, ``~/.LDB_Measure``.
    """
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        path = override
    else:
        path = _qt_app_data_dir() or os.path.join(
            os.path.expanduser("~"), "." + APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def user_config_file(name="settings.txt"):
    """Absolute path to one file inside :func:`user_config_dir`."""
    return os.path.join(user_config_dir(), name)


def _qt_app_data_dir():
    try:
        from PyQt6.QtCore import QStandardPaths
    except Exception:
        return None
    loc = QStandardPaths.StandardLocation.AppDataLocation
    path = QStandardPaths.writableLocation(loc)
    if not path:
        return None
    # AppDataLocation already ends in the application name once one is set on
    # QCoreApplication; if it is not set yet, pin our own leaf so the folder
    # is predictable either way.
    if os.path.basename(path) != APP_NAME:
        path = os.path.join(path, APP_NAME)
    return path
