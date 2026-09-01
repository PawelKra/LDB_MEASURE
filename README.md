# LDB_MEASURE

Soft for perfoming dendrochornological measurements of annual increments of trees.
To run this You will need measuring equipment (binoculars, encoder, counter and some mechanical parts that allow You to acquire measure precision at 0.01 mm).

## Instalation

Clone this repository and install the packages from `requirements.txt`
(runs on PyQt6 / Python 3.10+):

* matplotlib
* minimalmodbus
* numpy
* PyQt6 (+ PyQt6-Qt6, PyQt6-sip)
* pyserial
* pytest, pytest-qt, pytest-mock, pytest-cov, pytest-timeout

The `pytest*` packages are optional - install them only to run the tests.

### conda

```
conda create -n ldb python=3.12
conda activate ldb
pip install -r requirements.txt
python LDB_Measure.py
```

## Tests

```
pytest                 # picks up testy/ from pytest.ini
pytest --mpl           # also diff the chart against testy/baseline/*.png
```

`pytest.ini` sets `filterwarnings = error` (a resource leak or a PyQt6 /
matplotlib / numpy deprecation fails the run) and `testy/conftest.py` forces
`QT_QPA_PLATFORM=offscreen`, so the suite runs head-less (CI, SSH without X)
with no extra flags.

Property-based tests (`hypothesis`) live in `test_properties.py`; the chart
image-regression tests (`pytest-mpl`) in `test_charts_visual.py` - regenerate
their baselines in this env with
`pytest testy/test_charts_visual.py --mpl-generate-path=testy/baseline`.

GUI tests use `pytest-qt` (the `qtbot` fixture). Shared fixtures in
`conftest.py`:

* `fake_counter` - a scriptable stand-in for `devices.Device`; `.feed(120,
  135, ...)` queues the 1/100 mm increments a user would crank out, and each
  `read_measurement()` pops the next one. No hardware, no serial port.
* `main_window` / `loaded_window` - a live `LDB_Form` wired to `fake_counter`,
  optionally with three real samples loaded.
* `no_modals` - neutralises every blocking dialog (`QMessageBox`,
  `QInputDialog`, `QFileDialog`, sub-dialog `.exec()`), with knobs to steer
  the answers.

`devices.py` is unit-tested directly against a mocked `minimalmodbus` /
`pyserial` (`test_devices.py`).


## Releases / building installers

`.github/workflows/release.yml` builds the standalone apps on GitHub's
runners - no local toolchain, native binaries per platform:

| file | runner | covers |
|------|--------|--------|
| `LDB_Measure-windows-x64.exe`   | `windows-latest` | Windows 10/11 x64 |
| `LDB_Measure-macos-x86_64.dmg`  | `macos-13`       | Intel Macs |
| `LDB_Measure-macos-arm64.dmg`   | `macos-14`       | Apple Silicon Macs |

Push a `v*` tag (`git tag v0.1.0 && git push origin v0.1.0`) and the workflow
runs the test suite, builds with PyInstaller
(`packaging/LDB_Measure.spec`), and attaches the three files to a **draft**
GitHub Release for you to review and publish. `workflow_dispatch` builds the
same artifacts without a release; pull requests build (no release) as a smoke
check.

Local build (needs `pip install pyinstaller`):

```
pyinstaller --noconfirm packaging/LDB_Measure.spec
#  -> dist/LDB_Measure(.exe)        Windows / Linux
#  -> dist/LDB_Measure.app          macOS  (wrap: hdiutil create -volname LDB_Measure \
#                                            -srcfolder dist/LDB_Measure.app -ov -format UDZO x.dmg)
```

### First run

Settings live in a per-user file, editable from the in-app **Settings**
dialog and kept across launches:

* macOS &nbsp;`~/Library/Application Support/LDB_Measure/settings.txt`
* Windows `%APPDATA%\LDB_Measure\settings.txt`
* override with the `LDB_MEASURE_CONFIG_DIR` env var (portable / shared setups)

A fresh install has no settings - open **Settings** and set the counter
**device type** and **port** before measuring.

### Talking to the counter

No OS permission needs granting for a serial port - the app is not sandboxed,
so it just needs the USB-serial **driver** for the adapter's chip:

* **FTDI** - built into Windows and macOS, works out of the box
* **CP210x / CH340** - install the vendor driver once (on macOS it is a
  System Extension: approve it in *System Settings -> Privacy & Security*)

On macOS enter the port as `/dev/cu.usbserial-XXXX` (**not** `/dev/tty.*`,
which blocks waiting for carrier); on Windows it is `COMx`.

The unsigned builds trip Gatekeeper / SmartScreen on first launch: macOS -
right-click the app -> *Open* (or `xattr -dr com.apple.quarantine
LDB_Measure.app`); Windows - *More info -> Run anyway*. Neither affects serial
access.

##  Other usage

PM if You interested, and want to dig in, I will point You where to get price tag on equipment.


