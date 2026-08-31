"""Shared test fixtures.

Many tests reference data files by repo-root-relative paths
(``dane_test/proba_a.fh`` ...), so the whole session runs with the working
directory pinned to the repository root regardless of where pytest is invoked.
"""
import os
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _run_from_repo_root():
    old = os.getcwd()
    os.chdir(REPO_ROOT)
    try:
        yield
    finally:
        os.chdir(old)


@pytest.fixture
def data_dir():
    """Path to ``testy/data`` (golden JSON, multi.rwl, MIL fixtures)."""
    return pathlib.Path(__file__).resolve().parent / "data"
