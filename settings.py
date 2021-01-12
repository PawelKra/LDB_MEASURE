from settingWindow import Ui_settingWindow
from PyQt5.QtWidgets import QFileDialog, QDialog, QTableWidgetItem, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt
import copy
import sys


class Settings(QDialog, Ui_settingWindow):
    def __init__(self, configObject, parent=None):
        super(Settings, self).__init__(parent)
        self.setupUi(self)
        self.restart = False
        self.config = copy.deepcopy(configObject)
        self.orgConf = configObject

        # set current data from setting files
        self.g_sample_lineEdit.setText(self.config.p_pr)
        self.g_ref_lineEdit.setText(self.config.p_sr)
        self.g_working_lineEdit.setText(self.config.p_w)
        self.g_com.setText(str(self.config.port))
        self.g_impulses.setText(str(self.config.stala))
        if self.config.urz_licz == 'wo':
            self.g_counterType.setCurrentIndex(0)
        else:
            self.g_counterType.setCurrentIndex(1)

        self.populateDefPolTable()
        self.populateHeadersTable()

        # choose buttons signals
        self.g_sample_choose.clicked.connect(
            lambda x='s': self.chooseDirectory(x))
        self.g_ref_choose.clicked.connect(
            lambda x='r': self.chooseDirectory(x))
        self.g_working_choose.clicked.connect(
            lambda x='w': self.chooseDirectory(x))

        # lineEdit change signals
        self.connect(self.g_sample_lineEdit, pyqtSignal("textEdited(QString)"),
                     self.changedStackLineEditS)
        self.connect(self.g_ref_lineEdit, pyqtSignal("textEdited(QString)"),
                     self.changedStackLineEditR)
        self.connect(self.g_working_lineEdit, pyqtSignal("textEdited(QString)"),
                     self.changedStackLineEditW)

        # counter variables
        self.connect(self.g_impulses, pyqtSignal("textEdited(QString)"),
                     self.readImpulses)
        self.connect(self.g_com, pyqtSignal("textEdited(QString)"), self.readCOM)
        self.connect(self.g_counterType, pyqtSignal("currentIndexChanged(int)"),
                     self.counterChanged)

        self.g_ok.clicked.connect(self.saveSettings)

        self.g_firstDefPol.clicked.connect(lambda x='defpol': self.toFirst(x))
        self.g_firstHeader.clicked.connect(lambda x='headers': self.toFirst(x))
        self.g_lastDefPol.clicked.connect(lambda x='defpol': self.toLast(x))
        self.g_lastHeader.clicked.connect(lambda x='headers': self.toLast(x))
        self.g_upDefPol.clicked.connect(lambda x='defpol': self.toUp(x))
        self.g_upHeader.clicked.connect(lambda x='headers': self.toUp(x))
        self.g_downDefPol.clicked.connect(lambda x='defpol': self.toDown(x))
        self.g_downHeader.clicked.connect(lambda x='headers': self.toDown(x))

        self.g_defpol.cellChanged.connect(self.changedItemDefPol)
        self.g_delHeader.clicked.connect(self.deleteHeader)
        self.g_delDefPol.clicked.connect(self.deleteDefPol)
        self.g_addDefPol.clicked.connect(self.addDefPol)
        self.g_toHeaders.clicked.connect(self.toHeaders)

    def populateDefPolTable(self):
        # add data to defpol table and format it
        self.g_defpol.clear()
        self.g_defpol.setAlternatingRowColors(True)
        self.g_defpol.setSortingEnabled(False)
        self.g_defpol.setHorizontalHeaderLabels(["Value", "Type"])
        self.g_defpol.setRowCount(
            len(self.config.defpol_index[self.config.lenOrgDefPol:]))

        for i, it in enumerate(
                self.config.defpol_index[self.config.lenOrgDefPol:]):
            item = QTableWidgetItem()
            item.setText(it)
            self.g_defpol.setItem(i, 0, item)
            item2 = QTableWidgetItem()
            item2.setText(self.config.defpol[it])
            item2.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.g_defpol.setItem(i, 1, item2)

        self.g_defpol.resizeColumnsToContents()

    def populateHeadersTable(self):
        self.g_headers.clear()
        self.g_headers.setSortingEnabled(False)
        self.g_headers.setAlternatingRowColors(True)
        self.g_headers.setHorizontalHeaderLabels(["Headers"])
        self.g_headers.setRowCount(
            len(self.config.headers[self.config.lenOrgHeaders:]))
        for i, it in enumerate(self.config.headers[self.config.lenOrgHeaders:]):
            item = QTableWidgetItem()
            item.setText(it)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.g_headers.setItem(i, 0, item)

        self.g_headers.resizeColumnsToContents()

    def chooseDirectory(self, stackType):
        dir = str(QFileDialog.getExistingDirectory(None,
                                            'Choose Directory:',
                                             self.config.ostat_zapis,
                                             QFileDialog.ShowDirsOnly | \
                                                QFileDialog.DontResolveSymlinks
                                             )).decode(sys.stdout.encoding)
        if stackType == 's':
            self.config.p_pr = dir
            self.g_sample_lineEdit.setText(dir)
        elif stackType == 'w':
            self.config.p_w = dir
            self.g_working_lineEdit.setText(dir)
        elif stackType == 'r':
            self.config.p_r = dir
            self.g_ref_lineEdit.setText(dir)

    def changedStackLineEditS(self):
        self.config.p_pr = self.g_sample_lineEdit.text()

    def changedStackLineEditW(self):
        self.config.p_w = self.g_working_lineEdit.text()

    def changedStackLineEditR(self):
        self.config.p_sr = self.g_ref_lineEdit.text()

    def readImpulses(self):
        if str(self.g_impulses.text()).isdigit():
            self.config.stala = int(self.g_impulses.text())
        else:
            self.g_impulses.setText(str(self.config.stala))

    def readCOM(self):
        self.config.port = str(self.g_com.text())

    def counterChanged(self):
        if self.g_counterType.currentIndex() == 0:
            self.config.urz_licz = 'wo'
        else:
            self.config.urz_licz = 'pi'

    def saveSettings(self):
        output = ''

        self.orgConf.p_pr = self.config.p_pr
        output += 'S|' + str(self.config.p_pr).encode(sys.stdin.encoding) + '\n'
        self.orgConf.p_sr = self.config.p_sr
        output += 'R|' + str(self.config.p_sr).encode(sys.stdin.encoding) + '\n'
        self.orgConf.p_w = self.config.p_w
        output += 'W|' + str(self.config.p_w).encode(sys.stdin.encoding) + '\n'
        self.orgConf.headers = self.config.headers
        output += 'E|' + '|'.join(
            self.config.headers[self.config.lenOrgHeaders:]) + '\n'
        self.orgConf.defpol_index = self.config.defpol_index
        self.orgConf.defpol = self.config.defpol
        output += 'K'
        for item in self.config.defpol_index[self.config.lenOrgDefPol:]:
            output += '|' + ';'.join([str(item), str(self.config.defpol[item])])
        output += '\n'
        self.orgConf.stala = self.config.stala
        output += 'ST|' + str(self.config.stala) + '\n'
        self.orgConf.port = self.config.port
        output += 'PORT|' + str(self.config.port) + '\n'
        self.orgConf.urz_licz = self.config.urz_licz
        output += 'LICZ|' + str(self.config.urz_licz) + '\n'

        f = open('ustawienia.txt', 'w')
        f.write(output.encode(sys.stdin.encoding))

        self.restart = True
        self.close()

    def toFirst(self, table):
        self.moveElement(table, 'first')

    def toLast(self, table):
        self.moveElement(table, 'last')

    def toUp(self, table):
        self.moveElement(table, 'up')

    def toDown(self, table):
        self.moveElement(table, 'down')

    def moveElement(self, table, insert_position):
        tab = self.g_headers
        if table == 'defpol':
            tab = self.g_defpol

        tab.blockSignals(True)
        currentRow = tab.currentRow()

        position_dict = {'first': 0,
                         'last': tab.rowCount() - 1,
                         'up': currentRow - 1,
                         'down': currentRow + 1,
                         }

        if (currentRow == 0 and insert_position == 'up'):
            pass
        elif (currentRow == tab.rowCount()-1 and insert_position == 'down'):
            pass
        else:
            currentItem = tab.takeItem(currentRow, 0)
            if table == 'defpol':
                currentItem2 = tab.takeItem(currentRow, 1)
            tab.removeRow(currentRow)
            tab.insertRow(position_dict[insert_position])
            tab.setItem(position_dict[insert_position], 0, currentItem)
            if table == 'defpol':
                tab.setItem(position_dict[insert_position], 1, currentItem2)
            tab.setCurrentItem(currentItem)

        tab.blockSignals(False)
        self.syncTables()

    def changedItemDefPol(self):
        tab = self.g_defpol
        it = tab.item(tab.currentRow(), 0)

        if tab.currentColumn() == 1:
            it_modified = tab.item(tab.currentRow(), 1)
            if str(it_modified.text()) in ['T', 'I']:
                modification = str(it_modified.text())
                self.config.defpol[str(it.text())] = modification
            else:
                itorg = QTableWidgetItem(
                    self.config.defpol[
                        self.config.defpol_index[tab.currentRow()]])
                tab.setItem(tab.currentRow(), 1, itorg)
        else:
            oldName = self.config.defpol_index[
                tab.currentRow() + self.config.lenOrgDefPol]
            self.config.defpol_index[
                tab.currentRow() + self.config.lenOrgDefPol] = str(it.text())
            self.config.defpol[str(it.text())] = self.config.defpol[oldName]
            del self.config.defpol[oldName]

            if oldName in self.config.headers:
                it2 = QTableWidgetItem(str(it.text()))
                it2.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                oldIndex = self.config.headers.index(oldName)
                self.g_headers.setItem(oldIndex-self.config.lenOrgHeaders,
                                       0,
                                       it2
                                       )
                self.config.headers[oldIndex] = str(it.text())

        self.g_defpol.resizeColumnsToContents()
        self.g_headers.resizeColumnsToContents()

        self.syncTables()

    def syncTables(self):
        self.config.defpol_index = self.config.defpol_index[
            :self.config.lenOrgDefPol]
        self.config.headers = self.config.headers[:self.config.lenOrgHeaders]
        for i in range(self.g_defpol.rowCount()):
            it0 = self.g_defpol.item(i, 0)
            it1 = self.g_defpol.item(i, 1)
            self.config.defpol_index.append(str(it0.text()))
            self.config.defpol[str(it0.text())] = str(it1.text())

            if i < self.g_headers.rowCount():
                itH = self.g_headers.item(i, 0)
                self.config.headers.append(str(itH.text()))

    def deleteHeader(self):
        ile_wierszy = self.g_headers.rowCount()

        rowNumTab = range(0, ile_wierszy)
        rowNumTab.reverse()
        for i in rowNumTab:
            it = self.g_headers.item(i, 0)
            if it.isSelected():
                self.config.headers.remove(str(it.text()))
                self.g_headers.removeRow(i)

    def deleteDefPol(self):
        self.g_defpol.blockSignals(True)
        ile_wierszy = self.g_defpol.rowCount()
        rowNumTab = range(0, ile_wierszy)
        rowNumTab.reverse()

        for i in rowNumTab:
            it = self.g_defpol.item(i, 0)
            it1 = self.g_defpol.item(i, 1)
            if it.isSelected() or it1.isSelected():
                self.g_defpol.blockSignals(True)
                self.config.defpol_index.remove(str(it.text()))
                del self.config.defpol[str(it.text())]
                if str(it.text()) in self.config.headers:
                    self.config.headers.remove(str(it.text()))
                    self.populateHeadersTable()
                self.g_defpol.removeRow(i)
                self.g_defpol.blockSignals(False)
        self.g_defpol.blockSignals(False)

    def addDefPol(self):
        qtext, ok = QInputDialog.getText(self, 'Value', 'Field Name:')
        text = str(qtext)
        if ok:
            self.config.defpol_index.append(text)
            self.config.defpol[text] = 'T'
            lastRow = self.g_defpol.rowCount()
            self.g_defpol.insertRow(lastRow)
            it = QTableWidgetItem(text)
            it1 = QTableWidgetItem('T')
            it1.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.g_defpol.blockSignals(True)
            self.g_defpol.setItem(lastRow, 0, it)
            self.g_defpol.setItem(lastRow, 1, it1)
            self.g_defpol.blockSignals(False)

    def toHeaders(self):
        redraw = 0
        for i in range(self.g_defpol.rowCount()):
            it = self.g_defpol.item(i, 0)
            if it.isSelected() and not str(it.text()) in self.config.headers:
                redraw = 1
                self.config.headers.append(str(it.text()))

        if redraw:
            self.populateHeadersTable()
