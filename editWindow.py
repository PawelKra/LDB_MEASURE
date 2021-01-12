#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QInputDialog, QTableWidget, \
    QTableWidgetItem, QPushButton, QVBoxLayout, QGridLayout, \
    QSlider, QLabel, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg \
                                                                as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT \
                                                            as NavigationToolbar
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as pyplot
import copy


class edycja_proby(QDialog):
    def __init__(self, sample, defpol={}, defpol_order=[], parent=None):
        ''' defpol and defpol_order should contains the same values, it will
        not be checked in this class is it valid, pay attention to it'''
        super(edycja_proby, self).__init__(parent)

        # self.dane = globals()["daneW"][0]
        # self.defpol = globals()["daneW"][1]
        # globals()["daneW"] = []
        self.sample = copy.deepcopy(sample)
        self.sample._edytowany = 'E'
        self.org_sample = sample
        self.newName = self.sample.KeyCode()

        self.setWindowTitle("Sample: " + self.sample.KeyCode())
        self.resize(691, 749)
        self.setMinimumSize(QSize(691, 749))
        # self.setMaximumSize(QSize(691, 749))

        # Prepare headers
        self.defpol = defpol
        self.defpol_order = defpol_order
        self.prepareDefPol()
        self.selected = []  # list with index of selected ring in sample

        # ustawienie pol z danymi
        self.p_naglowek = QTableWidget()
        self.p_naglowek.setObjectName("p_naglowek")
        self.p_naglowek.setColumnCount(1)
        self.p_naglowek.setRowCount(len(self.headers))
        self.p_naglowek.setHorizontalHeaderLabels(["Value"])
        self.p_naglowek.setVerticalHeaderLabels(self.headers)
        self.p_naglowek.setAlternatingRowColors(True)
        self.p_naglowek.setSortingEnabled(False)

        self.p_dane = QTableWidget()
        self.p_dane.setObjectName("p_dane")
        self.p_dane.setColumnCount(10)
        self.p_dane.setHorizontalHeaderLabels(
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])

        self.dodaj = QPushButton("Add")
        self.usun = QPushButton("Delete")
        self.przerysuj = QPushButton("Redraw")
        self.podziel = QPushButton("Divide")
        self.polacz = QPushButton("Join")
        self.anuluj = QPushButton("Cancel")
        self.wykonaj = QPushButton("Update")

        self.vbl = QVBoxLayout()
        self.qmc = Qt4MplCanvas(self)
        self.ntb = NavigationToolbar(self.qmc, self)
        self.vbl.addWidget(self.qmc)
        self.vbl.addWidget(self.ntb)

        self.updateHeaderTable()
        self.wpisz_pomiary()
        self.przerysuj_wykres()

        # ustawiamy wyglad okna
        layout = QGridLayout()
        layout.addWidget(self.p_naglowek, 0, 0)

        layout1 = QGridLayout()
        layout1.addWidget(self.p_dane, 0, 0, 1, 5)
        layout1.addWidget(self.dodaj, 1, 0)
        layout1.addWidget(self.usun, 1, 1)
        layout1.addWidget(self.podziel, 1, 2)
        layout1.addWidget(self.polacz, 1, 3)
        layout1.addWidget(self.przerysuj, 1, 4)
        layout1.setRowMinimumHeight(1, 25)
        layout1.setRowStretch(0, 1)

        layout.addLayout(layout1, 0, 1)
        layout.addLayout(self.vbl, 1, 0, 1, 2)
        layout.addWidget(self.anuluj, 2, 0)
        layout.addWidget(self.wykonaj, 2, 1)
        layout.setColumnMinimumWidth(0, 290)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowMinimumHeight(0, 350)
        self.setLayout(layout)

        # Sygnaly
        self.connect(self.anuluj, pyqtSignal("clicked()"), self.schowaj)
        self.connect(self.wykonaj, pyqtSignal("clicked()"), self.wykonaj_odczytanie)
        self.connect(self.dodaj, pyqtSignal("clicked()"), self.dodaj_wartosc)
        self.connect(self.przerysuj, pyqtSignal("clicked()"), self.przerysuj_wykres)
        self.connect(self.usun, pyqtSignal("clicked()"), self.usun_wartosc)
        self.connect(self.podziel, pyqtSignal("clicked()"), self.podziel_wartosc)
        self.connect(self.polacz, pyqtSignal("clicked()"), self.polacz_wartosc)
        self.p_naglowek.cellChanged.connect(self.edytowana_kom_nagl)
        self.p_dane.itemSelectionChanged.connect(self.przerysuj_wykres)
        self.p_dane.cellChanged.connect(self.przerysuj_wykres)

    def prepareDefPol(self):
        """Prepare Headers for metadata,
        BEAWARE! measurements are delete on the end"""
        self.headers = [
                        'KeyCode',
                        'DateBegin',
                        'DateEnd',
                        'Length',
                        'Gat',
                        'SapWood',
                        'measurements',
                        ]
        add_table = []
        if len(self.defpol_order):
            add_table = self.defpol_order[:]
        elif len(self.defpol.keys()):
            add_table = sorted(list(self.defpol.keys()))
        else:
            add_table = sorted(self.sample.unikalneNaglowki())

        for val in add_table:
            if val not in self.headers:
                self.headers.append(val)
        self.headers.remove('measurements')

    def updateHeaderTable(self):
        # Dodaj wartosci wierszow dla tabeli naglowka proby
        self.p_naglowek.blockSignals(True)
        for i, val in enumerate(self.headers):
            if self.sample.wypiszMetadana(val):
                komorka = QTableWidgetItem(str(self.sample.wypiszMetadana(val)))
            else:
                komorka = QTableWidgetItem('---')

            if val == 'Length':
                komorka.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            self.p_naglowek.setItem(i, 0, komorka)
        self.p_naglowek.blockSignals(False)

    def wykonaj_odczytanie(self):
        # spisz cala probe z edytowanych tabel i zapisz ja do zmiennej globalnej
        # daneW
        self.odczytaj_dane(origin='org')
        self.newName = self.org_sample.KeyCode()
        self.hide()

    def przerysuj_wykres(self):
        self.odczytaj_dane()
        self.updateHeaderTable()
        self.chartData = [
                     [],  # X axis - years
                     [],  # Y axis - measurements
                    ]

        self.chartData[1] = self.sample.wypiszPomiary()
        self.chartData[0] = range(1, self.sample.Length() + 1)

        self.qmc.axes.clear()
        # draw sample curve
        self.qmc.axes.plot(self.chartData[0], self.chartData[1])

        # draw selected years
        Xpoints = []
        Ypoints = []
        self.selected = []
        j = 0
        for i in range(self.sample.Length()):
            if i == 11:
                j += 1
            item = self.p_dane.item(j, i-(j*10))
            if item.isSelected():
                Xpoints.append(i+1)
                self.selected.append(i)
                Ypoints.append(int(item.text()))
        self.qmc.axes.plot(Xpoints, Ypoints, 'ro')

        # formatting of support lines
        self.qmc.axes.xaxis.set_major_locator(MultipleLocator(10))
        self.qmc.axes.xaxis.set_minor_locator(MultipleLocator(2))

        # Prepare axis dimensions
        Xmax = 40
        if self.sample.Length() > 40:
            Xmax = self.sample.Length() + 2
        Ymax = max(self.sample.wypiszPomiary()) + 30
        self.qmc.axes.axis([0, Xmax, 0, Ymax])

        self.qmc.axes.xaxis.grid(
            True,
            'minor',
            linewidth=0.4,
            ls='-',
            color='0.20')
        self.qmc.axes.xaxis.grid(
            True,
            'major',
            linewidth=1,
            ls='-',
            color='0.80')
        self.qmc.axes.tick_params(axis='both', which='major', labelsize=10)
        self.qmc.axes.set_axisbelow(True)
        # ustawienie obszaru wykresu
        self.qmc.axes.set_position([0.03, 0.05, 0.96, 0.94])
        self.qmc.draw()

    def odczytaj_dane(self, origin='copy'):
        """update sample - read all metadata and measurements which could be
            altered by user. If origin of sample has to be modified use any
            string in origin
        """
        if origin == 'copy':
            target = self.sample
        else:
            target = self.org_sample

        for i, head in enumerate(self.headers):
            ins = self.p_naglowek.item(i, 0).text()
            if head not in ['Length'] and ins not in ['---', 0]:
                target.wpiszMetadana(
                    head,
                    ins
                    )

        rowNum = self.p_dane.rowCount()
        colNum = self.p_dane.columnCount()
        measurements = []
        check = 'ok'
        redraw = 0
        for w in range(rowNum):
            for k in range(colNum):
                item = self.p_dane.item(w, k)
                try:
                    if int(item.text()) != 0 and str(item.text()).isdigit:
                        measurements.append(int(item.text()))
                        # if after notOk we find number there is something wrong
                        # and we neef to reread measuremnts to tabel
                        if check == 'notOk':
                            redraw = 1
                except:
                    check = 'notOk'

        target.uaktualnijPom(measurements)
        if redraw == 1:
            self.wpisz_pomiary()

    def dodaj_wartosc(self):
        kk = 0
        self.ile_wierszy = self.p_dane.rowCount()
        self.ile_kol = self.p_dane.columnCount()
        for wiersz in range(self.ile_wierszy):
            for kolumna in range(self.ile_kol):
                item = self.p_dane.item(wiersz, kolumna)
                if self.p_dane.isItemSelected(item) == True and kk == 0:
                    kk = 1
                    text, ok = QInputDialog.getText(
                        self, 'Value', 'inser value: ')
                    if ok:
                        measurements = self.sample.wypiszPomiary()
                        measurements.insert((wiersz*10)+kolumna, int(text))
                        self.sample.uaktualnijPom(measurements)
        self.wpisz_pomiary()
        self.przerysuj_wykres()

    def usun_wartosc(self):
        sel = self.selected[:]
        sel.reverse()
        for s in sel:
            self.sample.usunOstatniPomiar(position=int(s))
        self.wpisz_pomiary()
        self.przerysuj_wykres()

    def wpisz_pomiary(self):
        # przygotowanie labelek poziomych dla tablicy z pomiarami
        self.w = (len(self.sample.wypiszPomiary()))/10
        if (len(self.sample.wypiszPomiary())) % 10 > 0:
            self.w += 1
        i = 0
        self.ww = []
        while i < self.w:
            self.ww.append(str(i*10))
            i += 1
        self.p_dane.blockSignals(True)
        self.p_dane.clear()
        self.p_dane.setRowCount(self.w)
        self.p_dane.setVerticalHeaderLabels(self.ww)
        self.p_dane.setAlternatingRowColors(True)
        self.p_dane.setSortingEnabled(False)

        # Dodajemy wartosci pomiarow
        i = 0
        j = 0
        k = 0
        measurements = self.sample.wypiszPomiary()
        while k < len(measurements):
            if j == 10:
                j = 0
                i += 1
            komorka = QTableWidgetItem(str(measurements[k]))
            self.p_dane.setItem(i, j, komorka)
            j += 1
            k += 1
        # uzupelniamy pozostale pola pustymi wartosciami
        while j % 10 != 0:
            komorka = QTableWidgetItem("")
            self.p_dane.setItem(i, j, komorka)
            j += 1
        self.p_dane.resizeColumnsToContents()
        self.p_dane.blockSignals(False)

    def podziel_wartosc(self):
        if len(self.selected) != 1:
            pass
        else:
            measurements = self.sample.wypiszPomiary()
            val = measurements[self.selected[0]]
            self.divideWindow = okno_podzialu(val)
            self.divideWindow.exec_()
            measurements.pop(self.selected[0])
            self.sample.uaktualnijPom(measurements)
            self.sample.dodajPomiar(self.divideWindow.val1,
                                    position=self.selected[0])
            self.sample.dodajPomiar(self.divideWindow.val0,
                                    position=self.selected[0])

            self.wpisz_pomiary()
            self.przerysuj_wykres()

    def polacz_wartosc(self):
        measurements = self.sample.wypiszPomiary()
        i = len(measurements) - 1
        selectionRange = []
        newMeasurements = []
        while i > -1:
            if i in self.selected:
                selectionRange.append(measurements[i])
            elif i not in self.selected:
                if len(selectionRange) > 0:
                    newMeasurements.append(sum(selectionRange))
                    selectionRange = []
                newMeasurements.append(measurements[i])
            i -= 1
        if len(selectionRange) > 0:
            newMeasurements.append(selectionRange)
        newMeasurements.reverse()
        self.sample.uaktualnijPom(newMeasurements)

        self.wpisz_pomiary()
        self.przerysuj_wykres()

    def schowaj(self):
        self.odczytaj_dane()
        self.hide()

    def edytowana_kom_nagl(self):
        # neccessary to maintain user specific date, otherwise it will be
        # shuflled
        row = self.p_naglowek.currentRow()
        self.p_naglowek.blockSignals(True)
        if self.headers[row] in ['DateBegin', 'DateEnd']:
            head_temp = self.headers[row]
            if head_temp == "DateBegin":
                self.sample.ustawDateBegin(
                    int(self.p_naglowek.item(row, 0).text()))
                it = QTableWidgetItem(str(self.sample.DateEnd()))
                self.p_naglowek.setItem(self.headers.index("DateEnd"), 0, it)
            if head_temp == "DateEnd":
                self.sample.ustawDateEnd(
                    int(self.p_naglowek.item(row, 0).text()))
                it = QTableWidgetItem(str(self.sample.DateBegin()))
                self.p_naglowek.setItem(self.headers.index("DateBegin"), 0, it)
        self.p_naglowek.blockSignals(False)
        self.przerysuj_wykres()


class okno_podzialu(QDialog):
    def __init__(self, value=0, parent=None):
        super(okno_podzialu, self).__init__(parent)

        self.aa = str(value)
        self.setWindowTitle("Divide Ringwidth")
        self.resize(150, 80)

        self.s = QSlider(Qt.Horizontal)
        self.s.setMinimum(1)
        self.s.setMaximum(int(self.aa))
        self.wart1 = QLabel("1")
        self.wart2 = QLabel(self.aa)
        self.lab = QLabel("Length = " + self.aa + " [1/100mm]")
        self.ok = QPushButton("OK")
        self.anuluj = QPushButton("Anuluj")

        layout = QGridLayout()
        layout.addWidget(self.wart1, 0, 0)
        layout.addWidget(self.s, 0, 1)
        layout.addWidget(self.wart2, 0, 2)
        layout.addWidget(self.lab, 1, 0, 1, 3)
        layout1 = QHBoxLayout()
        layout1.addWidget(self.ok)
        layout1.addWidget(self.anuluj)
        layout.addLayout(layout1, 2, 0, 1, 3)
        self.setLayout(layout)

        self.connect(self.s, pyqtSignal("valueChanged(int)"), self.uaktualnij)
        self.connect(self.anuluj, pyqtSignal("clicked()"), self.anulowanie)
        self.connect(self.ok, pyqtSignal("clicked()"), self.akceptuj)

    def uaktualnij(self):
        self.wart1.setText(str(self.s.value()))
        self.wart2.setText(str(int(self.aa) - self.s.value()))

    def akceptuj(self):
        self.val0 = self.s.value()
        self.val1 = int(self.aa) - self.s.value()
        self.hide()

    def anulowanie(self):
        self.close()


class Qt4MplCanvas(FigureCanvas):
    def __init__(self, parent):
        self.fig = pyplot.figure(dpi=100)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(
            self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
