"""respath - resource / user-config path resolution for source and frozen
(PyInstaller) runs."""
import os

import pytest

import respath


# --- resource_path (read-only bundled assets) -----------------------

def test_resource_path_is_next_to_the_sources_when_not_frozen():
    got = respath.resource_path("ikonki/UP.png")
    assert os.path.isabs(got)
    assert got == os.path.join(os.path.dirname(respath.__file__),
                               "ikonki", "UP.png")
    assert os.path.isfile(got)                       # the icon really ships


def test_resource_path_follows_meipass_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(respath.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert respath.resource_path("Monospace.ttf") == str(
        tmp_path / "Monospace.ttf")


# --- user_config_dir (writable settings) --------------------------

def test_env_override_wins_and_is_created(monkeypatch, tmp_path):
    target = tmp_path / "cfg" / "nested"
    monkeypatch.setenv(respath.CONFIG_DIR_ENV, str(target))

    got = respath.user_config_dir()

    assert got == str(target)
    assert os.path.isdir(got)                        # created on demand


def test_user_config_file_sits_inside_the_dir(monkeypatch, tmp_path):
    monkeypatch.setenv(respath.CONFIG_DIR_ENV, str(tmp_path))
    assert respath.user_config_file() == str(tmp_path / "settings.txt")
    assert respath.user_config_file("x.cfg") == str(tmp_path / "x.cfg")


def test_falls_back_to_qt_app_data_dir_without_the_env(monkeypatch):
    # don't hit the real makedirs here - just check the resolved shape
    monkeypatch.delenv(respath.CONFIG_DIR_ENV, raising=False)
    monkeypatch.setattr(respath.os, "makedirs", lambda *a, **k: None)

    got = respath.user_config_dir()

    assert os.path.isabs(got)
    assert os.path.basename(got) == respath.APP_NAME   # predictable leaf folder
