# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_LDB_ccresults.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1559, 528)
        font = QtGui.QFont()
        font.setFamily("Arial")
        Dialog.setFont(font)
        Dialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom))
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setMaximumSize(QtCore.QSize(500, 16777215))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setMinimumSize(QtCore.QSize(0, 41))
        self.label.setMaximumSize(QtCore.QSize(16777215, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setItalic(True)
        self.label.setFont(font)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.tableWidget_results = QtWidgets.QTableWidget(self.groupBox)
        font = QtGui.QFont()
        font.setFamily("Monospace")
        self.tableWidget_results.setFont(font)
        self.tableWidget_results.setAutoFillBackground(False)
        self.tableWidget_results.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom))
        self.tableWidget_results.setAlternatingRowColors(True)
        self.tableWidget_results.setShowGrid(False)
        self.tableWidget_results.setWordWrap(False)
        self.tableWidget_results.setObjectName("tableWidget_results")
        self.tableWidget_results.setColumnCount(1)
        self.tableWidget_results.setRowCount(1)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Monospace")
        item.setFont(font)
        self.tableWidget_results.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Monospace")
        item.setFont(font)
        self.tableWidget_results.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Monospace")
        font.setPointSize(8)
        item.setFont(font)
        self.tableWidget_results.setItem(0, 0, item)
        self.tableWidget_results.horizontalHeader().setVisible(False)
        self.tableWidget_results.horizontalHeader().setDefaultSectionSize(500)
        self.tableWidget_results.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableWidget_results)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_ok = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_ok.setMinimumSize(QtCore.QSize(0, 61))
        self.pushButton_ok.setMaximumSize(QtCore.QSize(341, 61))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.pushButton_ok.setFont(font)
        self.pushButton_ok.setObjectName("pushButton_ok")
        self.horizontalLayout.addWidget(self.pushButton_ok)
        self.pushButton_save = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_save.setMinimumSize(QtCore.QSize(0, 61))
        self.pushButton_save.setMaximumSize(QtCore.QSize(16777215, 61))
        self.pushButton_save.setObjectName("pushButton_save")
        self.horizontalLayout.addWidget(self.pushButton_save)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_cancel = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_cancel.setMinimumSize(QtCore.QSize(0, 61))
        self.pushButton_cancel.setMaximumSize(QtCore.QSize(151, 61))
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.horizontalLayout.addWidget(self.pushButton_cancel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2.addWidget(self.groupBox)
        self.widget = MplWidget(Dialog)
        self.widget.setMinimumSize(QtCore.QSize(921, 300))
        self.widget.setObjectName("widget")
        self.horizontalLayout_2.addWidget(self.widget)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Crossdate results"))
        self.groupBox.setTitle(_translate("Dialog", "Results"))
        self.label.setText(_translate("Dialog", "(Select row to redraw chart; double-click to select desired position for sample, will be applied after window is closed)"))
        item = self.tableWidget_results.verticalHeaderItem(0)
        item.setText(_translate("Dialog", "New Row"))
        item = self.tableWidget_results.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "New Column"))
        __sortingEnabled = self.tableWidget_results.isSortingEnabled()
        self.tableWidget_results.setSortingEnabled(False)
        item = self.tableWidget_results.item(0, 0)
        item.setText(_translate("Dialog", "Sample1   Ref2  CC   T    TBP   TH   GLK   GSL     CDI  OVL  DBeg  DEnd"))
        self.tableWidget_results.setSortingEnabled(__sortingEnabled)
        self.pushButton_ok.setText(_translate("Dialog", "Make changes permanent"))
        self.pushButton_save.setText(_translate("Dialog", "Save CC \n"
"raport to file"))
        self.pushButton_cancel.setText(_translate("Dialog", "Cancel"))
from mplwidget import MplWidget
