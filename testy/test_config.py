"""Unit tests for config.ReadConfig - the Qt-free settings parser.

Config file grammar (pipe-separated, one directive per line):
    S|<default catalogue path>
    ST|<impulses per mm, int>
    E|<comma-separated measurement headers>
    PORT|<serial port or interface>
    LICZ|<counter type: wo / pi>
"""
import os

import pytest

from config import ReadConfig


def test_missing_file_falls_back_to_defaults():
    c = ReadConfig('/no/such/config/file')
    assert c.dev == 'Absent'
    assert c.port == ''
    assert c.def_cat == ''
    assert c.impulses == 1
    assert c.headers == ['KeyCode', 'Species']
    assert c.lenOrgHeaders == 2


def test_empty_path_falls_back_to_defaults():
    assert ReadConfig('').headers == ['KeyCode', 'Species']


def test_parses_every_directive(tmp_path):
    cfg = tmp_path / 'settings.txt'
    cfg.write_text('\n'.join([
        'LICZ|wo',
        'PORT|COM7',
        'ST|100',
        'E|KeyCode,Species,SapWood,Bark',
        'S|/data/chronologies',
    ]))
    c = ReadConfig(str(cfg))
    assert c.dev == 'wo'
    assert c.port == 'COM7'
    assert c.impulses == 100
    assert c.def_cat == '/data/chronologies'
    assert c.headers == ['KeyCode', 'Species', 'SapWood', 'Bark']


def test_impulses_is_coerced_to_int(tmp_path):
    cfg = tmp_path / 's.txt'
    cfg.write_text('ST|250')
    c = ReadConfig(str(cfg))
    assert c.impulses == 250 and isinstance(c.impulses, int)


def test_header_directive_dedupes_against_existing_not_within_one_line(tmp_path):
    cfg = tmp_path / 's.txt'
    cfg.write_text('E|KeyCode,Species,Extra1,Extra2,Extra1')
    c = ReadConfig(str(cfg))
    # KeyCode / Species are dropped (already present); a value repeated *inside*
    # the same E| line slips through - known config.py limitation, the filter
    # only checks the pre-existing header list.
    assert c.headers == ['KeyCode', 'Species', 'Extra1', 'Extra2', 'Extra1']


def test_second_header_line_merges_into_the_list(tmp_path):
    cfg = tmp_path / 's.txt'
    cfg.write_text('E|KeyCode,Species,A\nE|B,Species,C')
    c = ReadConfig(str(cfg))
    assert c.headers == ['KeyCode', 'Species', 'A', 'B', 'C']


def test_write_config_round_trips(tmp_path):
    out = tmp_path / 'written.cfg'
    c = ReadConfig('')
    c.conf_file = str(out)              # absolute -> os.path.join keeps it as-is
    c.dev = 'pi'
    c.port = '/dev/ttyUSB0'
    c.impulses = 80
    c.def_cat = '/srv/rings'
    c.headers += ['Site', 'Elevation']
    c.write_config()

    assert out.is_file()
    assert not os.path.exists(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'written.cfg'))

    back = ReadConfig(str(out))
    assert back.dev == 'pi'
    assert back.port == '/dev/ttyUSB0'
    assert back.impulses == 80
    assert back.def_cat == '/srv/rings'
    assert back.headers == ['KeyCode', 'Species', 'Site', 'Elevation']
