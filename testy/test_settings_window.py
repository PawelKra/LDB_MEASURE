import os
import pytest
import classes
from pytestqt import qtbot
import sett_window
from config import ReadConfig
from PyQt5 import *


def test_load_settings(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)

    assert win.ui.tableWidget_headers.rowCount() == 5
    assert win.ui.lineEdit_com.text() == 'COM3'
    assert win.ui.g_sample_lineEdit.text() == 'test_path_to_cat'


def test_add_header(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)

    win.add_definition(text='test6')

    assert win.ui.tableWidget_headers.rowCount() == 6


def test_del_header(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)

    win.del_definition(text='test2')

    assert win.ui.tableWidget_headers.rowCount() == 4
    assert win.ui.tableWidget_headers.item(1, 0).text() == 'test3'


def test_move_one_down(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)
    win.move_one_down(text='test4')

    assert win.ui.tableWidget_headers.rowCount() == 5
    assert win.ui.tableWidget_headers.item(3, 0).text() == 'test5'
    assert win.ui.tableWidget_headers.item(4, 0).text() == 'test4'


def test_move_one_up(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)
    win.move_one_up(text='test3')

    assert win.ui.tableWidget_headers.rowCount() == 5
    assert win.ui.tableWidget_headers.item(1, 0).text() == 'test3'
    assert win.ui.tableWidget_headers.item(2, 0).text() == 'test2'


def test_move_to_top(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)
    win.move_to_top(text='test4')

    assert win.ui.tableWidget_headers.rowCount() == 5
    assert win.ui.tableWidget_headers.item(0, 0).text() == 'test4'
    assert win.ui.tableWidget_headers.item(3, 0).text() == 'test1'


def test_move_to_bottom(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)
    win.move_to_bottom(text='test2')

    assert win.ui.tableWidget_headers.rowCount() == 5
    assert win.ui.tableWidget_headers.item(1, 0).text() == 'test5'
    assert win.ui.tableWidget_headers.item(4, 0).text() == 'test2'


def test_modify_config(qtbot):
    conf = ReadConfig('')
    conf.dev = 'wo'
    conf.port = 'COM3'
    conf.def_cat = 'test_path_to_cat'
    conf.headers += ['test1', 'test2', 'test3', 'test4', 'test5']

    win = sett_window.SettWindow(conf)
    qtbot.addWidget(win)
    win.move_to_bottom(text='test2')
    win.move_to_top(text='test2')
    win.move_one_up(text='test1')
    win.add_definition(text='test99')
    win.del_definition(text='test4')
    win.write_changes(trun=True)

    assert win.ui.tableWidget_headers.rowCount() == 5
    assert win.ui.tableWidget_headers.item(0, 0).text() == 'test2'
    assert win.ui.tableWidget_headers.item(1, 0).text() == 'test5'
    assert win.ui.tableWidget_headers.item(2, 0).text() == 'test3'
    assert win.ui.tableWidget_headers.item(4, 0).text() == 'test99'
    assert win.setts.headers == ['KeyCode', 'Species',
                                 'test2', 'test5', 'test3', 'test1', 'test99']
