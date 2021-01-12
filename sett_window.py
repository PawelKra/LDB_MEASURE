from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QInputDialog, \
    QFileDialog
from ui_LDB_Settings import Ui_Dialog


class SettWindow(QDialog):
    def __init__(self, setts):
        super(QDialog, self).__init__()

        self.overwritten = False
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setts = setts  # settings readed file in config class

        # set values from config
        self.ui.g_sample_lineEdit.setText(self.setts.def_cat)
        self.ui.lineEdit_com.setText(self.setts.port)
        self.ui.lineEdit_imp.setText(str(self.setts.impulses))
        if self.setts.dev == 'wo':
            self.ui.comboBox_device.setCurrentIndex(0)
        else:
            self.ui.comboBox_device.setCurrentIndex(1)

        self.update_tw_header()

        self.ui.pushButton_defdir.clicked.connect(self.choose_dir)
        self.ui.pushButton_ok.clicked.connect(self.write_changes)
        self.ui.pushButton_cancel.clicked.connect(self.close)
        self.ui.g_addDefPol.clicked.connect(self.add_definition)
        self.ui.g_delDefPol.clicked.connect(self.del_definition)
        self.ui.g_upDefPol.clicked.connect(self.move_one_up)
        self.ui.g_downDefPol.clicked.connect(self.move_one_down)
        self.ui.g_lastDefPol.clicked.connect(self.move_to_bottom)
        self.ui.g_firstDefPol.clicked.connect(self.move_to_top)

    def update_tw_header(self):
        # syncs tw_headers with setts.def_headers
        self.ui.tableWidget_headers.blockSignals(True)
        self.ui.tableWidget_headers.clear()
        self.ui.tableWidget_headers.setColumnCount(1)
        self.ui.tableWidget_headers.setHorizontalHeaderLabels(['Attribute'])
        self.ui.tableWidget_headers.setRowCount(len(self.setts.headers)-2)
        self.ui.tableWidget_headers.setAlternatingRowColors(True)

        for i, it in enumerate(self.setts.headers[2:]):
            twi = QTableWidgetItem(it)
            self.ui.tableWidget_headers.setItem(i, 0, twi)

        self.ui.tableWidget_headers.blockSignals(False)

    def add_definition(self, text=False):
        if text is False:
            qtext, ok = QInputDialog.getText(self, 'Value', 'Attribute Name:')
            text = str(qtext)
        if text != '':
            rowcnt = self.ui.tableWidget_headers.rowCount()
            self.ui.tableWidget_headers.blockSignals(True)
            twi = QTableWidgetItem(text)
            self.ui.tableWidget_headers.setRowCount(rowcnt+1)
            self.ui.tableWidget_headers.setItem(rowcnt, 0, twi)
            self.ui.tableWidget_headers.blockSignals(False)

    def del_definition(self, text=False):
        rowcnt = self.ui.tableWidget_headers.rowCount()
        self.ui.tableWidget_headers.blockSignals(True)
        removed = 0
        itr = [x for x in range(0, rowcnt)]
        itr.reverse()

        for i in itr:
            it = self.ui.tableWidget_headers.item(i, 0)
            if it.isSelected() or it.text() == text:
                self.ui.tableWidget_headers.removeRow(i)
                removed += 1

        self.ui.tableWidget_headers.setRowCount(rowcnt-removed)
        self.ui.tableWidget_headers.blockSignals(False)

    def move_one_up(self, text=False):
        rowcnt = self.ui.tableWidget_headers.rowCount()
        self.ui.tableWidget_headers.blockSignals(True)
        for i in range(1, rowcnt):
            it = self.ui.tableWidget_headers.item(i, 0)
            if it.isSelected() or it.text() == text:
                txt0 = self.ui.tableWidget_headers.item(i-1, 0).text()
                twi = QTableWidgetItem(it.text())
                self.ui.tableWidget_headers.setItem(i-1, 0, twi)
                twi = QTableWidgetItem(txt0)
                self.ui.tableWidget_headers.setItem(i, 0, twi)

        self.ui.tableWidget_headers.blockSignals(False)

    def move_one_down(self, text=False):
        rowcnt = self.ui.tableWidget_headers.rowCount()
        self.ui.tableWidget_headers.blockSignals(True)
        for i in range(0, rowcnt-1):
            it = self.ui.tableWidget_headers.item(i, 0)
            if it.isSelected() or it.text() == text:
                txt0 = self.ui.tableWidget_headers.item(i+1, 0).text()
                twi = QTableWidgetItem(it.text())
                self.ui.tableWidget_headers.setItem(i+1, 0, twi)
                twi = QTableWidgetItem(txt0)
                self.ui.tableWidget_headers.setItem(i, 0, twi)

        self.ui.tableWidget_headers.blockSignals(False)

    def move_to_top(self, text=''):
        rowcnt = self.ui.tableWidget_headers.rowCount()
        self.ui.tableWidget_headers.blockSignals(True)
        for i in range(1, rowcnt):
            it = self.ui.tableWidget_headers.item(i, 0)
            if it.isSelected() or it.text() == text:
                txt0 = self.ui.tableWidget_headers.item(0, 0).text()
                twi = QTableWidgetItem(it.text())
                self.ui.tableWidget_headers.setItem(0, 0, twi)
                twi = QTableWidgetItem(txt0)
                self.ui.tableWidget_headers.setItem(i, 0, twi)

        self.ui.tableWidget_headers.blockSignals(False)

    def move_to_bottom(self, text=''):
        rowcnt = self.ui.tableWidget_headers.rowCount()
        self.ui.tableWidget_headers.blockSignals(True)
        for i in range(0, rowcnt-1):
            it = self.ui.tableWidget_headers.item(i, 0)
            if it.isSelected() or it.text() == text:
                txt0 = self.ui.tableWidget_headers.item(rowcnt-1, 0).text()
                twi = QTableWidgetItem(it.text())
                self.ui.tableWidget_headers.setItem(rowcnt-1, 0, twi)
                twi = QTableWidgetItem(txt0)
                self.ui.tableWidget_headers.setItem(i, 0, twi)
        self.ui.tableWidget_headers.blockSignals(False)

    def write_changes(self, trun=False):
        self.setts.dev = self.ui.comboBox_device.currentText()[:2]
        self.setts.port = str(self.ui.lineEdit_com.text())
        self.setts.impulses = int(self.ui.lineEdit_imp.text())
        self.setts.def_cat = str(self.ui.g_sample_lineEdit.text())

        rowcnt = self.ui.tableWidget_headers.rowCount()
        htemp = []
        for i in range(rowcnt):
            it = self.ui.tableWidget_headers.item(i, 0).text()
            if it != '':
                htemp.append(it)

        self.setts.headers = self.setts.headers[:2] + htemp
        if trun is False:
            self.setts.write_config()

            self.overwritten = True
        self.close()

    def choose_dir(self):
        dir = str(QFileDialog.getExistingDirectory(
            self,
            'Choose Directory:',
            self.setts.def_cat,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        ))
        if dir not in ['None', '', 'NULL']:
            self.ui.g_sample_lineEdit.setText(dir)

    def close(self):
        '''Hide window and abbandon all changes'''
        self.hide()
