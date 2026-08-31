"""Unit tests for :mod:`devices` - the measuring counter driver.

No hardware: ``minimalmodbus.Instrument`` and ``serial.Serial`` are mocked, so
the tests pin the driver's own logic (connection handling, the impulses->1/100mm
conversion, the zeroing commands) rather than any real port.
"""
import pytest

import devices
from config import ReadConfig


def _cfg(dev="wo", port="/dev/ttyUSB0", impulses=800):
    c = ReadConfig('')
    c.dev = dev
    c.port = port
    c.impulses = impulses
    return c


# --- WOBIT ("wo") modbus counter ----------------------------------------

@pytest.fixture
def wo_instrument(mocker):
    """Patched ``devices.mm.Instrument`` -> the MagicMock it returns."""
    inst = mocker.MagicMock(name="Instrument")
    mocker.patch.object(devices.mm, "Instrument", return_value=inst)
    return inst


def test_wo_connects_and_configures_serial(wo_instrument):
    dev = devices.Device(_cfg())

    assert dev.status == 1
    assert dev.inst is wo_instrument
    assert wo_instrument.serial.baudrate == 38400
    assert wo_instrument.serial.bytesize == 8
    assert wo_instrument.serial.stopbits == 1
    assert wo_instrument.mode == devices.mm.MODE_RTU


def test_wo_connection_failure_sets_status_zero(mocker):
    mocker.patch.object(devices.mm, "Instrument",
                        side_effect=OSError("no such port"))

    dev = devices.Device(_cfg())

    assert dev.status == 0


def test_wo_read_measurement_converts_impulses(wo_instrument):
    dev = devices.Device(_cfg(impulses=800))
    # low + (high << 16); first read is measured from the initial zero
    wo_instrument.read_register.side_effect = [800, 0]

    val = dev.read_measurement()

    assert val == 100                       # 800 impulses / 800 == 1.00 mm
    assert dev.readingB == 800              # baseline advanced for next read


def test_wo_read_measurement_is_relative_to_previous(wo_instrument):
    dev = devices.Device(_cfg(impulses=800))
    wo_instrument.read_register.side_effect = [800, 0, 2400, 0]

    first = dev.read_measurement()
    second = dev.read_measurement()

    assert first == 100                     # 0    -> 800
    assert second == 200                    # 800  -> 2400  == 1600/800 * 100


def test_wo_high_word_is_used(wo_instrument):
    dev = devices.Device(_cfg(impulses=1))
    dev.readingB = 0
    wo_instrument.read_register.side_effect = [0, 1]   # 0 + (1 << 16)

    val = dev.read_measurement()

    assert dev.readingA == 65536
    assert val == 65536 * 100


def test_wo_set_zeros_writes_reset_coil(wo_instrument):
    dev = devices.Device(_cfg())

    dev.set_zeros()

    wo_instrument.write_bit.assert_called_once_with(5000, 1, 5)
    assert dev.readingA == 0 and dev.readingB == 0


# --- AGH ("pi") serial counter ----------------------------------------

@pytest.fixture
def pi_serial(mocker):
    ser = mocker.MagicMock(name="Serial")
    ser.readline.return_value = b'<c>  1234567\r\n'
    mocker.patch.object(devices.serial, "Serial", return_value=ser)
    return ser


def test_pi_connects_and_reads_initial_counter(pi_serial):
    dev = devices.Device(_cfg(dev="pi", port="/dev/ttyACM0"))

    assert dev.status == 1
    assert dev.ser is pi_serial
    assert dev.readingB == 1234567
    pi_serial.write.assert_any_call(b'<c>')


def test_pi_connection_failure_sets_status_zero(mocker):
    mocker.patch.object(devices.serial, "Serial",
                        side_effect=OSError("port busy"))

    dev = devices.Device(_cfg(dev="pi"))

    assert dev.status == 0


def test_pi_read_measurement_parses_serial_reply(pi_serial):
    dev = devices.Device(_cfg(dev="pi", impulses=1))
    dev.readingB = 0
    pi_serial.readline.return_value = b'<c>  0000500\r\n'

    dev.read_measurement()

    assert dev.opened == 1               # port was (re)opened on first read
    pi_serial.write.assert_any_call(dev.comm)


def test_pi_set_zeros_sends_reset_command(pi_serial):
    dev = devices.Device(_cfg(dev="pi"))

    dev.set_zeros()

    pi_serial.write.assert_any_call(b'<d>')


def test_pi_zamknij_closes_port(pi_serial):
    dev = devices.Device(_cfg(dev="pi"))

    dev.zamknij()

    assert pi_serial.close.called
    assert dev.opened == 0


# --- absent counter --------------------------------------------------

def test_absent_device_never_touches_hardware(mocker):
    inst = mocker.patch.object(devices.mm, "Instrument")
    ser = mocker.patch.object(devices.serial, "Serial")

    dev = devices.Device(_cfg(dev="Absent"))

    assert dev.status == 0
    inst.assert_not_called()
    ser.assert_not_called()
