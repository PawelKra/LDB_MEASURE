# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_LDB_settings.ui'
#
# Created by: PyQt5 UI code generator 5.14.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(611, 854)
        font = QtGui.QFont()
        font.setFamily("Arial")
        Dialog.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setMinimumSize(QtCore.QSize(599, 70))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.g_sample_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.g_sample_lineEdit.setMinimumSize(QtCore.QSize(160, 0))
        self.g_sample_lineEdit.setObjectName("g_sample_lineEdit")
        self.horizontalLayout.addWidget(self.g_sample_lineEdit)
        self.pushButton_defdir = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_defdir.sizePolicy().hasHeightForWidth())
        self.pushButton_defdir.setSizePolicy(sizePolicy)
        self.pushButton_defdir.setMaximumSize(QtCore.QSize(61, 23))
        self.pushButton_defdir.setObjectName("pushButton_defdir")
        self.horizontalLayout.addWidget(self.pushButton_defdir)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setMinimumSize(QtCore.QSize(599, 121))
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setMinimumSize(QtCore.QSize(110, 16))
        self.label.setMaximumSize(QtCore.QSize(110, 16777215))
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.comboBox_device = QtWidgets.QComboBox(self.groupBox_2)
        self.comboBox_device.setMinimumSize(QtCore.QSize(200, 22))
        self.comboBox_device.setMaximumSize(QtCore.QSize(200, 16777215))
        self.comboBox_device.setObjectName("comboBox_device")
        self.comboBox_device.addItem("")
        self.comboBox_device.addItem("")
        self.horizontalLayout_4.addWidget(self.comboBox_device)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setMinimumSize(QtCore.QSize(110, 16))
        self.label_2.setMaximumSize(QtCore.QSize(110, 16777215))
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_5.addWidget(self.label_2)
        self.lineEdit_com = QtWidgets.QLineEdit(self.groupBox_2)
        self.lineEdit_com.setObjectName("lineEdit_com")
        self.horizontalLayout_5.addWidget(self.lineEdit_com)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setMinimumSize(QtCore.QSize(110, 16))
        self.label_3.setMaximumSize(QtCore.QSize(110, 16777215))
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_6.addWidget(self.label_3)
        self.lineEdit_imp = QtWidgets.QLineEdit(self.groupBox_2)
        self.lineEdit_imp.setObjectName("lineEdit_imp")
        self.horizontalLayout_6.addWidget(self.lineEdit_imp)
        self.verticalLayout_2.addLayout(self.horizontalLayout_6)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.groupBox_3 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_3.setMinimumSize(QtCore.QSize(290, 0))
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.tableWidget_headers = QtWidgets.QTableWidget(self.groupBox_3)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.tableWidget_headers.setFont(font)
        self.tableWidget_headers.setObjectName("tableWidget_headers")
        self.tableWidget_headers.setColumnCount(0)
        self.tableWidget_headers.setRowCount(0)
        self.horizontalLayout_7.addWidget(self.tableWidget_headers)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.g_addDefPol = QtWidgets.QPushButton(self.groupBox_3)
        self.g_addDefPol.setMinimumSize(QtCore.QSize(31, 31))
        self.g_addDefPol.setMaximumSize(QtCore.QSize(31, 31))
        self.g_addDefPol.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("ikonki/editadd.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.g_addDefPol.setIcon(icon)
        self.g_addDefPol.setObjectName("g_addDefPol")
        self.verticalLayout_4.addWidget(self.g_addDefPol)
        self.g_delDefPol = QtWidgets.QPushButton(self.groupBox_3)
        self.g_delDefPol.setMinimumSize(QtCore.QSize(31, 31))
        self.g_delDefPol.setMaximumSize(QtCore.QSize(31, 31))
        self.g_delDefPol.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("ikonki/editremove.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.g_delDefPol.setIcon(icon1)
        self.g_delDefPol.setObjectName("g_delDefPol")
        self.verticalLayout_4.addWidget(self.g_delDefPol)
        self.g_firstDefPol = QtWidgets.QPushButton(self.groupBox_3)
        self.g_firstDefPol.setMinimumSize(QtCore.QSize(31, 31))
        self.g_firstDefPol.setMaximumSize(QtCore.QSize(31, 31))
        self.g_firstDefPol.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("ikonki/TOP.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.g_firstDefPol.setIcon(icon2)
        self.g_firstDefPol.setObjectName("g_firstDefPol")
        self.verticalLayout_4.addWidget(self.g_firstDefPol)
        self.g_upDefPol = QtWidgets.QPushButton(self.groupBox_3)
        self.g_upDefPol.setMinimumSize(QtCore.QSize(31, 31))
        self.g_upDefPol.setMaximumSize(QtCore.QSize(31, 31))
        self.g_upDefPol.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("ikonki/UP.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.g_upDefPol.setIcon(icon3)
        self.g_upDefPol.setObjectName("g_upDefPol")
        self.verticalLayout_4.addWidget(self.g_upDefPol)
        self.g_downDefPol = QtWidgets.QPushButton(self.groupBox_3)
        self.g_downDefPol.setMinimumSize(QtCore.QSize(31, 31))
        self.g_downDefPol.setMaximumSize(QtCore.QSize(31, 31))
        self.g_downDefPol.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("ikonki/DOWN.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.g_downDefPol.setIcon(icon4)
        self.g_downDefPol.setObjectName("g_downDefPol")
        self.verticalLayout_4.addWidget(self.g_downDefPol)
        self.g_lastDefPol = QtWidgets.QPushButton(self.groupBox_3)
        self.g_lastDefPol.setMinimumSize(QtCore.QSize(31, 31))
        self.g_lastDefPol.setMaximumSize(QtCore.QSize(31, 31))
        self.g_lastDefPol.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("ikonki/LAST.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.g_lastDefPol.setIcon(icon5)
        self.g_lastDefPol.setObjectName("g_lastDefPol")
        self.verticalLayout_4.addWidget(self.g_lastDefPol)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem1)
        self.horizontalLayout_7.addLayout(self.verticalLayout_4)
        self.verticalLayout.addWidget(self.groupBox_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_ok = QtWidgets.QPushButton(Dialog)
        self.pushButton_ok.setObjectName("pushButton_ok")
        self.horizontalLayout_2.addWidget(self.pushButton_ok)
        self.pushButton_cancel = QtWidgets.QPushButton(Dialog)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.horizontalLayout_2.addWidget(self.pushButton_cancel)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Settings Window"))
        self.groupBox.setTitle(_translate("Dialog", "Default Directory"))
        self.g_sample_lineEdit.setText(_translate("Dialog", "C:\\"))
        self.pushButton_defdir.setText(_translate("Dialog", "Choose"))
        self.groupBox_2.setTitle(_translate("Dialog", "Counter Settings"))
        self.label.setText(_translate("Dialog", "Counter type:"))
        self.comboBox_device.setItemText(0, _translate("Dialog", "wo - WoBIT counter"))
        self.comboBox_device.setItemText(1, _translate("Dialog", "pi - AGH Counter"))
        self.label_2.setText(_translate("Dialog", "COM:"))
        self.lineEdit_com.setText(_translate("Dialog", "COM#"))
        self.label_3.setText(_translate("Dialog", "impulses / mm"))
        self.lineEdit_imp.setText(_translate("Dialog", "800"))
        self.groupBox_3.setTitle(_translate("Dialog", "Header Definitions"))
        self.pushButton_ok.setText(_translate("Dialog", "OK"))
        self.pushButton_cancel.setText(_translate("Dialog", "Cancel"))