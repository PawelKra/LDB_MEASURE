# LDB_MEASURE

Desktop software for dendrochronological measurement of tree-ring widths.
You crank a rotary encoder mounted on a measuring stage under a stereo
microscope; a counter turns encoder steps into micrometres, and LDB_MEASURE
records ring after ring, draws the curve, cross-dates series against
references, and builds mean chronologies.

To measure you need the hardware: stereo microscope, a measuring stage with a
rotary encoder, and a supported counter (see **Connecting the counter**).
Without a counter the app still runs - you can open, view, edit, cross-date
and export existing series, just not record new ones.

---

## Install

### Prebuilt app (easiest)

Download the file for your system from the repository's **Releases** page:

| file | system |
|------|--------|
| `LDB_Measure-windows-x64.exe`  | Windows 10 / 11, 64-bit |
| `LDB_Measure-macos-arm64.dmg`  | Apple Silicon Macs (M1 and later) |

Intel Macs are not covered by a prebuilt binary - build it locally (see
*Building the standalone apps*) or run the app from source.

The builds are **not code-signed**, so the first launch needs one extra step:

* **macOS** - right-click the app and choose *Open* (once), or run
  `xattr -dr com.apple.quarantine /Applications/LDB_Measure.app`.
* **Windows** - on the SmartScreen prompt click *More info -> Run anyway*.

This does not affect access to the counter.

### From source

Use a **conda** environment. On Linux this is the recommended way - it avoids
mismatches between the pip PyQt6 wheel and the system Qt / X libraries; on
macOS and Windows a plain `venv` works just as well.

```bash
conda create -n ldb python=3.12
conda activate ldb
pip install -r requirements.txt
python LDB_Measure.py
```

`venv` alternative (macOS / Windows):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python LDB_Measure.py
```

Runs on Python 3.10-3.12 (3.12 recommended). Runtime dependencies:
`PyQt6` (+ `PyQt6-Qt6`, `PyQt6-sip`), `numpy`, `matplotlib`, `pyserial`,
`minimalmodbus`. The `pytest*` and `hypothesis` lines in `requirements.txt`
are only needed to run the test suite; `pyinstaller` only to build the
standalone apps.

**Linux:** if Qt reports *"could not load the Qt platform plugin xcb"*,
install the X client libraries it links against - on Debian / Ubuntu:

```bash
sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 \
                 libxcb-keysyms1 libxcb-shape0
```

---

## Configuration

Settings are stored in a per-user file you edit from the in-app **Settings**
window; they persist across launches and updates.

| system | location |
|--------|----------|
| macOS   | `~/Library/Application Support/LDB_Measure/settings.txt` |
| Windows | `%APPDATA%\LDB_Measure\settings.txt` |
| Linux   | `~/.local/share/LDB_Measure/settings.txt` |

Set the environment variable `LDB_MEASURE_CONFIG_DIR` to keep the file
somewhere else (a portable install, a shared lab configuration).

On a fresh install there is no file yet and the status bar says so - open
**Settings** and set:

* **Counter type** - `wo` (WoBIT) or `pi` (AGH); see below
* **COM** - the serial port / device path
* **impulses / mm** - encoder resolution, used to convert steps to
  micrometres (e.g. `800`)
* **Default Directory** - where Open / Save start
* **Header Definitions** - extra metadata columns for each series (saved only
  in the `.fh` format)

### settings.txt format

Plain text, one pipe-separated directive per line (written automatically by
the Settings window; you rarely edit it by hand):

```
LICZ|wo                     # counter type: wo | pi
PORT|/dev/cu.usbserial-1420 # serial port
ST|800                      # impulses per mm
E|KeyCode,Species,Site      # extra per-series metadata columns
S|/home/you/rings           # default catalogue
```

---

## Connecting the counter

A serial port needs **no operating-system permission** - the app is not
sandboxed, so nothing has to be granted. What matters is that the USB-serial
adapter's **driver** is installed so the port appears:

* **FTDI** chips - driver is built into Windows and macOS, works out of the box.
* **CP210x**, **CH340/CH341** - install the vendor's driver once. On macOS
  this is a *System Extension*: after installing, approve it in
  *System Settings -> Privacy & Security* (a reboot may be required).

Port name to enter in Settings:

* **macOS** - `/dev/cu.usbserial-XXXX` (use `cu.*`, **not** `tty.*` - the
  `tty` device blocks waiting for a carrier signal). List them with
  `ls /dev/cu.*`.
* **Windows** - `COMx` (check Device Manager).
* **Linux** - `/dev/ttyUSB0`, `/dev/ttyACM0`, ... (add yourself to the
  `dialout` group: `sudo usermod -aG dialout $USER`, then re-login).

Supported counters:

| type | counter | link | notes |
|------|---------|------|-------|
| `wo` | WoBIT   | Modbus RTU (via `minimalmodbus`), 38400 baud |
| `pi` | AGH counter | raw serial, 57600 baud, `<c>` / `<d>` commands |

---

## Measuring workflow

1. **New sequence** (Measurements panel) opens a session and zeroes the
   counter. Turn the encoder one ring at a time and press **Read measure**
   (or the space bar) to append each width. **Delete last measure** drops the
   most recent; **clean** clears the current session.
2. Optionally mark the first sapwood ring with **enter ring no.** - on
   **End of session** it is stored as a sapwood-ring *count*.
3. **End of session** commits the series to the table and the chart.
4. Select rows and use **Crossdate** to correlate them (against each other,
   or a loaded reference set) or **Mean from selected** (needs two or more)
   to build a mean chronology.
5. Edit individual rings from the chart: right-click a curve with exactly one
   series selected -> *Delete / Add / Modify*, plus *Undo / Redo ring edit*.
6. **Save** writes the series; the format dropdown picks the on-disk format
   (`.fh` keeps metadata; `.txt` / `.avr` are one file per series).

---

## Building the standalone apps

### With GitHub Actions (no local toolchain)

`.github/workflows/release.yml` builds native binaries on GitHub's runners:

| artifact | runner |
|----------|--------|
| `LDB_Measure-windows-x64.exe`  | `windows-latest` |
| `LDB_Measure-macos-arm64.dmg`  | `macos-14` (Apple Silicon) |

* **Tag `v*`** (`git tag v0.1.0 && git push origin v0.1.0`) - runs the tests,
  builds both, and attaches them to a **draft** GitHub Release for you to
  check and publish.
* **Run workflow** (Actions tab, `workflow_dispatch`) - builds the two
  artifacts without making a release; use it for a dry run.
* **Pull request** - builds only, as a smoke check.

PyInstaller does not cross-compile, so each target is built on its own runner.
Intel macOS (`macos-13`) is left out - GitHub's Intel runners are being retired
and were unschedulable for hours; add it back to the matrix in
`release.yml` if you need an `x86_64` `.dmg`.

### Locally

```bash
pip install pyinstaller
pyinstaller --noconfirm packaging/LDB_Measure.spec
#  Windows / Linux -> dist/LDB_Measure(.exe)   one self-contained file
#  macOS           -> dist/LDB_Measure.app
```

Wrap the macOS bundle in a disk image:

```bash
hdiutil create -volname LDB_Measure -srcfolder dist/LDB_Measure.app \
               -ov -format UDZO dist/LDB_Measure.dmg
```

The recipe bundles `ikonki/` and `Monospace.ttf` and resolves them through
`respath.resource_path()`; `respath.py` also decides where `settings.txt`
lives. `multiprocessing.freeze_support()` runs first in `__main__` so a frozen
build's cross-dating worker processes do not relaunch the GUI.

---

## Tests

```bash
pytest                 # collects testy/ (see pytest.ini)
pytest --mpl           # also pixel-diff the charts against testy/baseline/*.png
```

`pytest.ini` sets `filterwarnings = error` (a resource leak or a
PyQt6 / matplotlib / numpy deprecation fails the run) and `conftest.py` forces
`QT_QPA_PLATFORM=offscreen`, so everything runs head-less with no extra flags.

The GUI tests drive the real window through `pytest-qt`. Key fixtures in
`testy/conftest.py`:

* `fake_counter` - a scriptable stand-in for `devices.Device`; `.feed(120,
  135, ...)` queues the 1/100 mm steps a user would crank, each
  `read_measurement()` pops the next. No hardware, no serial port.
* `main_window` / `loaded_window` - a live `LDB_Form` wired to `fake_counter`,
  optionally with three real sample files loaded.
* `no_modals` - neutralises every blocking dialog, with knobs to steer the
  answers.
* an autouse fixture points `LDB_MEASURE_CONFIG_DIR` at a throwaway directory
  so the suite never touches your real `settings.txt`.

Property-based tests (`hypothesis`) are in `test_properties.py`; chart
image-regression baselines (`pytest-mpl`) in `testy/baseline/` - regenerate
them in this environment with
`pytest testy/test_charts_visual.py --mpl-generate-path=testy/baseline`.

One test, `test_properties.py::test_corellate_is_bounded_and_never_raises`,
currently fails: a numpy `RuntimeWarning` for a degenerate correlation window,
promoted to an error by `filterwarnings`. It is deselected in CI and tracked
separately.

---

## Repository layout

| file(s) | role |
|---------|------|
| `LDB_Measure.py` | entry point, main window, wiring |
| `panel_*.py` | mixin classes, one per area of the main window (sample, measurements, chart, device, places) |
| `classes.py` | Qt-free model + statistics: `Sequence`, `DataBase`, cross-dating, means |
| `dendro/io.py` | file-format registry (`.fh` `.pos` `.rwl` `.avr` `.r*` `.txt`, plus `.csv` / `.json` export) |
| `devices.py` | counter drivers (`minimalmodbus` / `pyserial`) |
| `config.py` | `settings.txt` parser / writer |
| `respath.py` | resource and user-config paths (source vs. frozen) |
| `sett_window.py`, `ccres_window.py`, `ccopt_window.py`, `editWindow.py` | secondary dialogs |
| `ui_LDB_*.py` | `pyuic6`-generated layouts (edit the `.ui` files, then regenerate) |
| `mplwidget.py` | the embedded matplotlib canvas |
| `packaging/` | PyInstaller spec |
| `testy/` | test suite |

---

## Contact

Interested in the method or the hardware? PM the author and there are pointers
on where to source the equipment.
