# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build recipe for LDB_Measure.

Run from the repository root:

    pyinstaller --noconfirm packaging/LDB_Measure.spec

Output:
  * Windows / Linux -> dist/LDB_Measure(.exe)   one self-contained file
  * macOS           -> dist/LDB_Measure.app     bundle (wrap in a .dmg after)

Version string comes from the LDB_VERSION env var (the git tag in CI),
defaulting to 0.0.0 for a local build.
"""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).resolve().parent          # SPECPATH == <repo>/packaging

_v = os.environ.get("LDB_VERSION", "0.0.0")
VERSION = _v[1:] if _v.startswith("v") else _v

# read-only assets that the app loads at run time via respath.resource_path()
datas = [
    (str(ROOT / "ikonki"), "ikonki"),
    (str(ROOT / "Monospace.ttf"), "."),
]
binaries = []

# pyserial picks its backend at import time by platform; name every one so the
# frozen build keeps them all. minimalmodbus + the mpl Qt backend are imported
# only indirectly.
hiddenimports = [
    "serial",
    "serial.tools.list_ports",
    "serial.tools.list_ports_common",
    "serial.tools.list_ports_posix",
    "serial.tools.list_ports_windows",
    "minimalmodbus",
    "matplotlib.backends.backend_qtagg",
]

# numpy 2.x (numpy._core.*) and matplotlib (mpl-data, backends) are not fully
# picked up by the stock hooks on a clean build - pull everything.
for _pkg in ("numpy", "matplotlib"):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

excludes = ["tkinter", "pytest", "_pytest", "pytest_qt", "hypothesis"]

a = Analysis(
    [str(ROOT / "LDB_Measure.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name="LDB_Measure",
        console=False,
        argv_emulation=False,
        target_arch=None,               # native: x86_64 on macos-13, arm64 on macos-14
        icon=None,
    )
    coll = COLLECT(
        exe, a.binaries, a.datas,
        strip=False, upx=False,
        name="LDB_Measure",
    )
    app = BUNDLE(
        coll,
        name="LDB_Measure.app",
        icon=None,
        bundle_identifier="org.ldb.ldbmeasure",
        version=VERSION,
        info_plist={
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "LSMinimumSystemVersion": "11.0",
            "NSHighResolutionCapable": True,
            "LSApplicationCategoryType": "public.app-category.education",
        },
    )
else:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.datas, [],
        name="LDB_Measure",
        console=False,
        upx=False,
        icon=None,
    )
