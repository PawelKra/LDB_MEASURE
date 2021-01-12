import os
import pytest
import classes
from pytestqt import qtbot
import LDB_Measure
from PyQt5 import *
from PySide2.QtTest import QTest


def test_add_sequence_to_measure(qtbot):
    win = LDB_Measure.LDB_Form()
    qtbot.addWidget(win)
    win.testrun = True
    # qtbot.mouseClick(win.ui.pushButton_new_sample, QtCore.Qt.LeftButton)
    # qtbot.mouseClick(win.ui.pushButton_new_sequence, QtCore.Qt.LeftButton)
    win.new_sample()
    win.new_sequence()

    assert win.saved is False
    assert win.order == ['R1'] and win.stack['s']['R1'].KeyCode() == 'R1'
    assert win.opened.KeyCode() == 'R1'


def test_add_close_sequence_to_measure(qtbot):
    win = LDB_Measure.LDB_Form()
    qtbot.addWidget(win)
    win.testrun = True
    # qtbot.mouseClick(win.ui.pushButton_new_sample, QtCore.Qt.LeftButton)
    # qtbot.mouseClick(win.ui.pushButton_new_sequence, QtCore.Qt.LeftButton)
    # qtbot.mouseClick(win.ui.pushButton_end_measures, QtCore.Qt.LeftButton)
    win.new_sample()
    win.new_sequence()
    win.end_sequence()

    assert win.saved is False
    assert win.order == ['R1'] and win.stack['s']['R1'].KeyCode() == 'R1'
    assert win.opened is False


def test_delete_sequence(qtbot):
    win = LDB_Measure.LDB_Form()
    win.test_samples = ['dane_test/deska1_3.fh',
                        'dane_test/STAR42.AVR',
                        'dane_test/STAR5.AVR',
                        ]
    qtbot.addWidget(win)
    win.load_samples()
    it = win.ui.tableWidget_meas.item(1, 0)
    it.setSelected(True)
    win.ui.tableWidget_meas.setItem(1, 0, it)

    win.delete_sequences()

    assert win.order == ['R1', 'R3']
    assert len(win.stack['s'].keys()) == 2


def test_update_sequence(qtbot):
    win = LDB_Measure.LDB_Form()
    win.testrun = True
    win.test_samples = ['dane_test/deska1_3.fh',
                        'dane_test/STAR42.AVR',
                        'dane_test/STAR5.AVR',
                        ]
    qtbot.addWidget(win)
    win.load_samples()
    it = win.ui.tableWidget_meas.item(1, 0)
    it.setSelected(True)
    win.continue_sequence()

    assert win.opened.KeyCode() == 'R2'


def test_sync_db_to_twMeas(qtbot):
    win = LDB_Measure.LDB_Form()
    win.testrun = True
    win.test_samples = ['dane_test/deska1_3.fh',
                        'dane_test/STAR42.AVR',
                        'dane_test/STAR5.AVR',
                        ]
    qtbot.addWidget(win)
    win.load_samples()
    win.stack.base['s']['R3'].setDateBegin(333)
    win.sync_db_to_twmeas()

    it = win.ui.tableWidget_meas.item(2, 1).text()
    assert it == '333'


def test_sync_tWMeas_to_db(qtbot):
    win = LDB_Measure.LDB_Form()
    win.testrun = True
    win.test_samples = ['dane_test/deska1_3.fh',
                        'dane_test/STAR42.AVR',
                        'dane_test/STAR5.AVR',
                        ]
    qtbot.addWidget(win)
    win.load_samples()
    win.stack.base['s']['R3'].setDateBegin(333)
    win.sync_db_to_twmeas()

    twi = QtWidgets.QTableWidgetItem('333')
    win.ui.tableWidget_meas.setItem(2, 1, twi)
    win.ui.tableWidget_meas.cellChanged.emit(2, 1)
    assert win.stack.base['s']['R3'].DateBegin() == 333


# def test_key_press_left(qtbot):
#     win = LDB_Measure.LDB_Form()
#     win.testrun = True
#     win.test_samples = ['dane_test/deska1_3.fh',
#                         'dane_test/STAR42.AVR',
#                         'dane_test/STAR5.AVR',
#                         ]
#     qtbot.addWidget(win)
#     win.load_samples()
#     win.ui.tableWidget_meas.item(2, 0).setSelected(True)
#     db0 = win.stack.base['s']['R3'].DateBegin()
#     QTest.keyClick(win.ui.centralwidget, QtCore.Qt.Key_F3)
#     db1 = win.stack.base['s']['R3'].DateBegin()
#
#     assert db0 == db1 + 1
