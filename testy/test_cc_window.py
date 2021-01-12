import os
import pytest
import classes
from ccres_window import Results
from pytestqt import qtbot
from PyQt5 import *
from PySide2.QtTest import QTest


def test_choose_cc_job(qtbot):
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    st.add_seq('s', f1)

    win = Results(st)
    win.choose_cc_job(allcc=True)
    qtbot.addWidget(win)

    assert win.grp == 0
    assert win.sst == 's' and win.rst == 's'


def test_crossdate_simple(qtbot):
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    f1['proba_a'].setDateBegin(1688)
    st.add_seq('s', f1)

    win = Results(st)
    win.choose_cc_job(allcc=True)
    win.crossdate()
    # qtbot.mouseClick(win.ui.pushButton_new_sample, QtCore.Qt.LeftButton)

    assert win.res_dict['proba_a']['proba_b'][0][7]+1688 == 1711
    assert len(win.res_dict['proba_a']['proba_b']) == 15


def test_format_report(qtbot):
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    f1['proba_a'].setDateBegin(1688)
    st.add_seq('s', f1)

    win = Results(st)
    win.choose_cc_job(allcc=True)
    win.crossdate()
    # qtbot.mouseClick(win.ui.pushButton_new_sample, QtCore.Qt.LeftButton)

    win.load_result()
    # assert win.ui.tableWidget_results.rowCount() == 25
    assert win.out_dict['proba_a'][2][-3] == '21    '


def test_redraw_chart(qtbot):
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    f1['proba_a'].setDateBegin(1688)
    st.add_seq('s', f1)

    win = Results(st)
    win.choose_cc_job(allcc=True)
    win.crossdate()

    win.load_result()
    win.ui.tableWidget_results.item(8, 0).setSelected(True)
    win.ui.tableWidget_results.cellClicked.emit(8, 0)

    assert win.ui.widget.canvas.ax.get_xlim() == (164, 288)


def test_doubleclicked_change_color(qtbot):
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    f1['proba_a'].setDateBegin(1688)
    st.add_seq('s', f1)

    win = Results(st)
    win.choose_cc_job(allcc=True)
    win.crossdate()

    win.load_result()
    win.ui.tableWidget_results.cellDoubleClicked.emit(8, 0)

    # assert win.ui.tableWidget_results.rowCount() == 25
    clr = QtGui.QColor(255, 0, 0, 127)
    assert win.ui.tableWidget_results.item(
        8, 0).background().color().getRgb() == clr.getRgb()


def test_save_report(qtbot):
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    f1['proba_a'].setDateBegin(1688)
    st.add_seq('s', f1)

    win = Results(st)
    win.choose_cc_job(allcc=True)
    win.crossdate()
    win.load_result()
    # qtbot.mouseClick(win.ui.pushButton_save, QtCore.Qt.LeftButton)
    win.save_txt(p2f='dane_test/test_raport_save.txt')

    # assert win.ui.tableWidget_results.rowCount() == 25
    assert os.path.exists('dane_test/test_raport_save.txt')


def test_make_changes_permanent(qtbot):
    st = classes.DataBase(['s'])
    f1 = classes.read_fh(['dane_test/proba_a.fh',
                          'dane_test/proba_b.fh',
                          'dane_test/deska1_3.fh',
                          ])
    f1['proba_a'].setDateBegin(1688)
    st.add_seq('s', f1)

    win = Results(st)
    win.choose_cc_job(allcc=True)
    win.crossdate()

    win.load_result()
    win.ui.tableWidget_results.cellDoubleClicked.emit(8, 0)

    sname = win.ui.tableWidget_results.item(8, 0).text().split(' ')[0]
    dbeg0 = win.stack.base['s'][sname].DateBegin()

    qtbot.addWidget(win)
    # QTest.mouseClick(win.ui.pushButton_ok, QtCore.Qt.LeftButton)
    # qtbot.mouseClick(win.ui.pushButton_ok, QtCore.Qt.LeftButton)
    win.make_permanent()


    assert dbeg0 != win.stack.base['s'][sname].DateBegin()
