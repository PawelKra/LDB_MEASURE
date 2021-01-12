from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QFileDialog, QMessageBox
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from ui_LDB_Ccresults import Ui_Dialog
from ccopt_window import Options
import classes
import matplotlib
import datetime


class Results(QDialog):
    def __init__(self, stack):
        super(QDialog, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.stack = stack  # DataBase object
        self.selected = {}  # dict with names of selected smp on stacks
        self.changed = False  # flag set to true if any seq is modified

        self.out_dict = {}  # dict with formated and sorted calculations
        self.out_dict = {}  # dict with raw cc results [ref][smp]
        self.result = []  # list with lines ready to write to tW

        # crosscorellation options
        self.sst = ''  # name of stack with samples
        self.rst = ''  # name of stack with refs
        self.grp = 0  # grouping of results, default (all samps & ref)
        self.crl = 15  # corellation per set (sample&ref)

        # setup start time
        self.dt0 = datetime.datetime.now()

        # signals
        self.ui.pushButton_ok.clicked.connect(self.make_permanent)
        self.ui.pushButton_cancel.clicked.connect(self.cancel)
        self.ui.pushButton_save.clicked.connect(self.save_txt)
        self.ui.tableWidget_results.cellClicked.connect(self.redraw)
        self.ui.tableWidget_results.cellDoubleClicked.connect(
                                                self.user_doubleclick)

    def set_selected(self, selected={}):
        '''option for passing names of selected samples from stacks
        selected={'s': ['s1', 's2', ...], }
        '''
        self.selected = selected

    def choose_cc_job(self, allcc=False):
        '''Shows dialog to user for selecting crossdate options
        all - option for correlating all samples from one stack (onlyone stack
            should be defined in stack (True/False)
        '''

        # update selected dict to be compatible with stack keys
        for key in self.stack.base.keys():
            if key not in self.selected:
                self.selected[key] = [x for x in self.stack.base[key].keys()]

        # setup dialog, will be needed later
        self.frm = Options()
        self.frm.ui.comboBox_samps.clear()
        self.frm.ui.comboBox_samps.addItems(
            sorted(list([x for x in self.stack.base.keys()])))
        self.frm.ui.comboBox_refs.clear()
        self.frm.ui.comboBox_refs.addItems(
            sorted(list([x for x in self.stack.base.keys()])))

        # if there is only one stack in db
        if allcc and len(self.stack.base.keys()) == 1:
            self.rst = self.sst = [x for x in self.stack.base.keys()][0]
            self.grp = 0
            return

        else:
            # self.frm.show()
            self.frm.exec_()

            self.sst = self.frm.ui.comboBox_samps.currentText()
            self.rst = self.frm.ui.comboBox_refs.currentText()
            self.crl = int(self.frm.ui.label_2.text())
            self.grp = self.frm.ui.comboBox_opt.currentIndex()

    def make_permanent(self):
        '''User confirm that selected options should be updated to base data
        '''
        twr = self.ui.tableWidget_results
        sel = [twr.item(i, 0).text() for i in range(twr.rowCount())
               if twr.item(i, 0).background().color().toRgb() ==
               QColor(255, 0, 0, 127)]
        for it in sel:
            raw = list(filter(lambda x: x != '', it.split(' ')))
            sname = raw[0]
            rname = raw[1]
            smps = self.stack.seq_from_stack(self.sst, [sname])
            refs = self.stack.seq_from_stack(self.rst, [rname])

            # get Sequence objects
            if len(smps) != 1 or len(refs) != 1:
                continue

            dbeg = int(raw[-2])
            smps[sname].setDateBegin(dbeg)
            self.changed = True
            self.cancel()

    def cancel(self):
        self.hide()

    def save_txt(self, p2f=''):
        '''saves txt in file pointed by user'''
        testrun = False
        if p2f in [False, '']:
            p2f = QFileDialog.getSaveFileName(self, 'Save Report as:', '')[0]
        else:
            testrun = True

        if p2f in '':
            return

        fl = open(p2f, 'w')
        fl.write('\n'.join(self.result))
        fl.close()

        if not testrun:
            msgBox = QMessageBox()
            msgBox.setText('Report saved!')
            msgBox.exec_()

    def user_doubleclick(self, row, col):
        '''user doubleclicked one row, method checks if this is new selection
        or older and acordingly adds this raw to list with changes and set
        background of row.
        '''
        twr = self.ui.tableWidget_results
        it = twr.item(row, col)

        try:
            raw = list(filter(lambda x: x != '', it.text().split(' ')))
            sname = raw[0]
            rname = raw[1]
        except IndexError:
            return

        smps = self.stack.seq_from_stack(self.sst, [sname])
        refs = self.stack.seq_from_stack(self.rst, [rname])

        # get Sequence objects
        if len(smps) != 1 or len(refs) != 1:
            return

        color = QColor(255, 0, 0, 127)
        if it.background().color().getRgb() == (255, 0, 0, 127):
            color = QColor(0, 0, 0)
        twr.item(row, col).setBackground(color)
        self.changed = True

    def crossdate(self):
        '''Crossdate samples with refs provided by user, creating result list
        '''

        # dict with results, after performing corellations data will be grouped
        # accordingly to user specs
        # dict = {'s1': {'s2': [corr_result], 's3': []},
        #         's2': {'s1': [], ...}, ...   }
        res_dict = {}

        # create list of samples and references from selected items
        refs = [val for val in self.stack.seq_from_stack(
            self.rst, self.selected[self.rst]).values()
            if val.Length() > 29
        ]
        smps = [val for val in self.stack.seq_from_stack(
            self.sst, self.selected[self.sst]).values()
            if val.Length() > 29
        ]

        # MAIN JOB - takes longest to do
        # TODO: Check if can be optimized!!!
        for ref in refs:
            for smp in smps:
                # avoid crosdating same sample
                if smp.KeyCode() == ref.KeyCode():
                    continue

                # check if corelation wasnt compute other side if do continue
                if smp.KeyCode() in res_dict:
                    if ref.KeyCode() in res_dict[smp.KeyCode()]:
                        continue

                crslt = classes.corellate(smp, ref, self.crl)
                if ref.KeyCode() not in res_dict:
                    res_dict[ref.KeyCode()] = {}
                if smp.KeyCode() not in res_dict:
                    res_dict[smp.KeyCode()] = {}

                res_dict[ref.KeyCode()][smp.KeyCode()] = crslt
                resr = [x[:7] + [-x[7], x[8], x[10], x[9]] for x in crslt]
                res_dict[smp.KeyCode()][ref.KeyCode()] = resr

        self.refs = refs
        self.smps = smps
        self.res_dict = res_dict

    def load_result(self):
        '''Loads formated results to tableWidget for user convinience'''
        result = []

        if self.grp == 0:
            self.group_by_ref()
        elif self.grp == 1:
            self.group_by_samp()
        else:
            self.group_by_none()

        result = []
        for key in sorted(self.out_dict.keys()):
            result += ['']
            result += [''.join(row) for row in self.out_dict[key]]

        result += [] + [''+10*'-'+'[ End Report ]'+10*'-']

        dd = datetime.datetime.now() - self.dt0
        result_head = [
            10*'-'+'[ CrossDate Report ]'+10*'-',
            'Date/Time: '+self.dt0.isoformat()[:-7],
            'Job time: '+str(dd.seconds)+' seconds',
            'Minimu Left|Right ovl = 25',
            'Grouping: '+self.frm.ui.comboBox_opt.itemText(self.grp),
        ]

        result = result_head + result
        self.result = result

        self.ui.tableWidget_results.blockSignals(True)
        self.ui.tableWidget_results.clear()
        self.ui.tableWidget_results.setColumnCount(1)
        self.ui.tableWidget_results.setRowCount(len(result))

        fnt = QFont('Helvetica')
        # fnt.setFamily('Monospace')
        fnt.setPointSize(10)
        for i, row in enumerate(result):
            twi = QTableWidgetItem(row)
            twi.setFont(fnt)
            twi.setForeground(QColor('red'))
            twi.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.tableWidget_results.setItem(i, 0, twi)
            self.ui.tableWidget_results.item(i, 0).setFont(fnt)
            self.ui.tableWidget_results.item(i, 0).setBackground(
                                                    QColor(0, 0, 0))

        self.ui.tableWidget_results.blockSignals(False)

    def extract_flat(self, di):
        """Extracts from dic correlation tables"""

        corrlist = []
        for y in di.values():
            corrlist += y
        return corrlist

    def group_by_ref(self):
        for ref in self.refs:
            rname = ref.KeyCode()
            tlist = sorted(self.extract_flat(self.res_dict[rname]),
                           key=lambda x: x[6],
                           reverse=True)[:self.crl]
            self.out_dict[rname] = self.format_lines(tlist)

    def group_by_samp(self):
        for smpl in self.smps:
            sname = smpl.KeyCode()
            tlist = sorted(self.extract_flat(self.res_dict[sname]),
                           key=lambda x: x[6],
                           reverse=True)[:self.crl]
            self.out_dict[sname] = self.format_lines(tlist)

    def group_by_none(self):
        for smpl in self.smps:
            sname = smpl.KeyCode()
            for ref, val in self.res_dict[sname].items():
                if sname not in self.out_dict:
                    self.out_dict[sname] = []
                self.out_dict[sname] += self.format_lines(val)

    def format_lines(self, tlist):
        lout = []
        cc = classes.format_text_spaces
        ltmp = max([len(x[-2]) for x in tlist]) + 1
        len_smp_name = ltmp if ltmp > 7 else 7
        ltmp = max([len(x[-1]) for x in tlist]) + 1
        len_ref_name = ltmp if ltmp > 6 else 6
        lout = [[''], [cc('Sample', len_smp_name),
                       cc('Ref.', len_ref_name),
                       cc('Ovl'),
                       cc('Glk'),
                       cc('GSL'),
                       cc('CC'),
                       cc('T'),
                       cc('TH'),
                       cc('TBP'),
                       cc('CDI'),
                       cc('DateB'),
                       cc('DateE'),
                       ]]

        for row in tlist:
            lout += [[
                cc(row[-2], len_smp_name),  # smpl
                cc(row[-1], len_ref_name),  # ref
                cc(str(row[8])),  # OVL
                cc(str(row[4])),  # GLK
                cc(str(row[5])),  # GSL
                cc(str(row[0])),  # cc
                cc(str(row[3])),  # t
                cc(str(row[2])),  # tH
                cc(str(row[1])),  # tBP
                cc(str(row[6])),  # CDI
                cc(str(self.stack.base[self.rst][row[-1]].DateBegin()+row[7])),
                cc(str(self.stack.base[self.rst][row[-1]].DateBegin() +
                       row[7] +
                       self.stack.base[self.sst][row[-2]].Length())),
            ]]
        return lout

    def redraw(self):
        '''redraws chart with data selected by user.
        Triggered after user chose one of rows in tw_results,
        draw sample and ref in position from correlation
        '''
        # find first selected
        try:
            sel = [self.ui.tableWidget_results.item(i, 0).text() for i in
                   range(self.ui.tableWidget_results.rowCount())
                   if self.ui.tableWidget_results.item(i, 0).isSelected()
                   ][0]

            raw = list(filter(lambda x: x != '', sel.split(' ')))
            sname = raw[0]
            rname = raw[1]
        except IndexError:
            return

        self.ui.widget.canvas.ax.clear()  # clean widet

        smps = self.stack.seq_from_stack(self.sst, [sname])
        refs = self.stack.seq_from_stack(self.rst, [rname])

        # get Sequence objects
        if len(smps) != 1 or len(refs) != 1:
            return
        smpl = smps[sname]
        ref = refs[rname]
        dbeg = int(raw[-2])

        chdata = []  # list with data for every smpl to put on chart
        # it is important to know how may years we want to draw because mpl has
        # limitation of showing year ticks, to many and it will crash
        min_year = min([dbeg, ref.DateBegin()]) - 2  # min year on chart
        # max year on chart
        max_year = max([dbeg+smpl.Length(), ref.DateEnd()]) + 7

        chdata.append([
            [y for y in range(ref.DateBegin(), ref.DateEnd()+1)],
            [x for x in ref.measurements()],
            ref.KeyCode()
        ])
        chdata.append([
            [y for y in range(dbeg, dbeg+smpl.Length())],
            [x for x in smpl.measurements()],
            smpl.KeyCode()
        ])

        for i, tab in enumerate(chdata):
            self.ui.widget.canvas.ax.plot(tab[0], tab[1], linewidth=2-i)
            self.ui.widget.canvas.ax.text(
                max(tab[0])+1, tab[1][-1], tab[2])

        self.ui.widget.canvas.ax.get_yaxis().set_visible(False)
        self.ui.widget.canvas.ax.set_xlim(min_year, max_year)
        locator = 5 if (max_year-min_year) < 999 else 25
        self.ui.widget.canvas.ax.get_xaxis().set_minor_locator(
            matplotlib.ticker.MultipleLocator(locator))
        self.ui.widget.canvas.ax.grid(axis='x', which='both')
        self.ui.widget.canvas.ax.grid(axis='x', which='minor', linewidth=0.2)
        self.ui.widget.canvas.ax.set_position([0.001, 0.07, 0.99, 0.91])

        self.ui.widget.canvas.draw()
