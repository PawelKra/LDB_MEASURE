import os
import pytest
import classes
from pytestqt import qtbot
import LDB_Measure
from PyQt5 import *


def test_open_window(qtbot):
    win = LDB_Measure.LDB_Form()
    qtbot.addWidget(win)
    # qtbot.mouseClick(win.ui.pushButton_new_sample, QtCore.Qt.LeftButton)
    win.new_sample()
    assert win.saved is True


def test_load_sample(qtbot):
    win = LDB_Measure.LDB_Form()
    win.test_samples = ['dane_test/deska1_3.fh',
                        'dane_test/STAR42.AVR',
                        'dane_test/STAR5.AVR',
                        ]
    qtbot.addWidget(win)
    win.load_samples()
    # qtbot.mouseClick(win.ui.pushButton_load_sample, QtCore.Qt.LeftButton)
    assert win.saved is False
    assert len(win.stack['s'].keys()) == 3
    assert len(win.order) == 3
    assert list(win.stack.seq_from_stack('s').values())[0].Length() > 0


def test_save_sample(qtbot):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    files = [
        'test_save_sample.fh',
        'test_save_sample.txt',
        'test_save_sample.avr',
        'test_save_sample_R.fh',
        'test_save_sample_R1.avr',
        'test_save_sample_R1.txt',
        'test_save_sample_R2.avr',
        'test_save_sample_R2.txt',
        'test_save_sample_R3.avr',
        'test_save_sample_R3.txt',
    ]
    for fi in files:
        if os.path.exists(os.path.join(base_dir, 'dane_test', fi)):
            os.remove(os.path.join(base_dir, 'dane_test', fi))

    win = LDB_Measure.LDB_Form()
    win.test_samples = ['dane_test/deska1_3.fh',
                        'dane_test/STAR42.AVR',
                        'dane_test/STAR5.AVR',
                        ]
    win.setts.def_cat = os.path.join(base_dir, 'dane_test')
    win.ui.lineEdit_cat_samples.setText(win.setts.def_cat)
    win.ui.lineEdit_cat_means.setText(win.setts.def_cat)
    qtbot.addWidget(win)
    win.load_samples()

    seq = classes.Sequence({'KeyCode': 'M1', 'DateBegin': 1,
                            'measurements': [1, 2, 3, 4, 6, 8, 9]
                            })

    win.order.append('M1')
    win.stack.add_seq('s', {'M1': seq})
    win.add_meas_to_tWMeas(seq)

    t1 = QtWidgets.QTableWidgetItem('test_save_sample')
    win.ui.tableWidget_attr.setItem(0, 0, t1)
    # qtbot.mouseClick(win.ui.pushButton_save_sample, QtCore.Qt.LeftButton)
    win.save_sample()
    win.ui.comboBox_format.setCurrentIndex(1)
    # qtbot.mouseClick(win.ui.pushButton_save_sample, QtCore.Qt.LeftButton)
    win.save_sample()
    win.ui.comboBox_format.setCurrentIndex(2)
    # qtbot.mouseClick(win.ui.pushButton_save_sample, QtCore.Qt.LeftButton)
    win.save_sample()

    assert win.saved is True
    assert len(win.stack['s'].keys()) == 4
    assert len(win.order) == 4
    assert os.path.exists(os.path.join(win.setts.def_cat,
                                       'test_save_sample_R.fh'))
    assert os.path.exists(os.path.join(win.setts.def_cat,
                                       'test_save_sample_R1.txt'))
    assert os.path.exists(os.path.join(win.setts.def_cat,
                                       'test_save_sample_R2.avr'))
    assert os.path.exists(os.path.join(win.setts.def_cat,
                                       'test_save_sample_R3.avr'))
    assert os.path.exists(os.path.join(win.setts.def_cat,
                                       'test_save_sample_R1.avr'))
