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


##  Other usage

PM if You interested, and want to dig in, I will point You where to get price tag on equipment.


