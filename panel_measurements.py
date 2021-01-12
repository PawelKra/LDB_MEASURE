from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from user_decorators import UserDecorators
from ccres_window import Results
import classes


class PanelMeasurements:
    @UserDecorators.should_be_closed
    @UserDecorators.select_measure_button
    def new_sequence(self):
        '''Open connection to device, set counter to null and prepare all
        structures to store measures from user, set state opened as True
        '''
        if not self.setup_device():
            return

        seq = classes.Sequence()
        self.add_meas_to_tWMeas(seq)

        self.opened = seq  # set current seq to update mesures later
        self.saved = False

    @UserDecorators.should_be_closed
    @UserDecorators.select_measure_button
    def continue_sequence(self):
        '''setup currently selected sequence to continue measures
        '''
        # check if we have attached any device on port
        if not self.setup_device():
            return

        selected, rows = self.selected_twmeas_rows()
        if selected != 1:
            msgBox = QMessageBox()
            msgBox.setText('For continue, there should be selected '
                           'one sample from measurement panel!'
                           )
            msgBox.exec_()
            return

        # get object with selected sequence
        name = self.ui.tableWidget_meas.item(rows[0], 0).text()
        seq = self.stack.seq_from_stack('s', [name])[name]

        self.opened = seq  # set current seq to update measures later
        self.update_textedit_meas()
        self.saved = False

    @UserDecorators.should_be_closed
    def delete_sequences(self):
        '''deletes selected sequences from tableWidget_meas, and from database
        it cant be undone
        '''
        selected, rows = self.selected_twmeas_rows()
        rows.reverse()  # reverse rows to delete from backward

        self.ui.tableWidget_meas.blockSignals(True)
        for i in rows:
            name = self.ui.tableWidget_meas.item(i, 0).text()
            if self.stack.del_seq('s', [name]):
                self.ui.tableWidget_meas.removeRow(i)
                self.order.remove(name)
        self.ui.tableWidget_meas.blockSignals(False)
        self.redraw_chart()

    @UserDecorators.should_be_closed
    def correlate_sequences(self):
        '''correlate selected sequences from tableWidget_meas, shows new
        windows with stats, where user can see infos
        '''

        try:
            corw = Results(self.stack)
            corw.choose_cc_job(allcc=True)
            corw.crossdate()
            corw.load_result()
            corw.exec_()
            self.sync_db_to_twmeas()
        except Exception:
            msgBox = QMessageBox()
            msgBox.setText('Ooops! Something goes wrong! Is it me or You?')
            msgBox.exec_()
            return

    @UserDecorators.should_be_closed
    def create_mean(self):
        '''calculate mean from selected samples from tableWidget_meas and
        adds new sequence to database
        '''
        selected, rows = self.selected_twmeas_rows()
        names = [self.ui.tableWidget_meas.item(i, 0).text() for i in rows]
        mean = self.stack.calculate_mean('s', names)
        mean.set_meta('KeyCode', 'M'+str(self.nextM()))
        self.order.append(mean.KeyCode())
        self.stack.add_seq('s', {1: mean})

        self.add_meas_to_tWMeas(mean)

    def nextR(self):
        '''return next int to add to R sample
        '''
        try:
            val = max([int(x[1:]) for x in self.order if x[0] == 'R'])
        except ValueError:
            return '1'
        return str(val + 1)

    def nextM(self):
        '''return next int to add to M mean
        '''
        try:
            val = max([int(x[1:]) for x in self.order if x[0] == 'M'])
        except ValueError:
            return '1'
        return str(val + 1)

    def add_meas_to_tWMeas(self, mseq):
        '''Method adds new meas to tableWidget_meas, adds name to order
        list and adds meas to database.
        Redraw chart
        mseq - Sequence object
        '''
        # if this is readed Sequence, set new name to it
        # and add it to all structures
        if mseq.KeyCode() not in self.order:
            mseq.set_meta('LabNotes', mseq.KeyCode())
            mseq.set_meta('KeyCode', 'R'+self.nextR())
            self.order.append(mseq.KeyCode())
            self.stack.add_seq('s', {mseq.KeyCode(): mseq})

        tw = self.ui.tableWidget_meas
        tw.blockSignals(True)
        row = self.order.index(mseq.KeyCode())
        tw.setRowCount(len(self.order))

        cols = [
            str(mseq.KeyCode()),
            str(mseq.DateBegin()),
            str(mseq.DateEnd()),
            str(mseq.Length()),
            str(mseq.SapWood()),
            str(mseq.pith_growth()),
            str(mseq.export_meta('Refs')),
            str(mseq.export_meta('LabNotes')),
        ]
        for j, val in enumerate(cols):
            cell = QTableWidgetItem(val if val != 'Unknown' else '')
            if j in [0, 3]:
                cell.setFlags(Qt.ItemIsEditable | Qt.ItemIsSelectable)
            tw.setItem(row, j, cell)
        tw.blockSignals(False)
        tw.resizeColumnsToContents()
        self.redraw_chart()
        self.saved = False

    def selected_twmeas_rows(self):
        '''Returns int of all selected rows in tableWidget_meas, and
        numbers of rows
        returns cnt_rows, [list of ints]
        '''
        rng = self.ui.tableWidget_meas.selectedRanges()
        rows = []
        for bb in [list(range(x.topRow(), x.bottomRow()+1)) for x in rng]:
            rows += bb

        return len(rows), sorted(list(set(rows)))

    def sync_twmeas_to_db(self, row=-1, col=-1):
        '''called when user changed something in tableWidget_meas, and it
        needs to be synced with database. Work both sides
        write = writes from tw to db (def)
        read = puts db values to tw
        '''
        # check if dateb or datee is valid, put it in database or write proper
        # one from db
        twi = False
        if col == 1:
            txt = self.ui.tableWidget_meas.item(row, col).text()
            if txt.isdigit():
                self.stack.base['s'][self.order[row]].setDateBegin(int(txt))
                self.sync_db_to_twmeas([
                    self.stack.base['s'][self.order[row]].KeyCode()
                ])
            else:
                twi = QTableWidgetItem(
                    str(self.stack.base['s'][self.order[row]].DateBegin()))

        if col == 2:
            txt = self.ui.tableWidget_meas.item(row, col).text()
            if txt.isdigit():
                self.stack.base['s'][self.order[row]].setDateEnd(int(txt))
                self.sync_db_to_twmeas([
                    self.stack.base['s'][self.order[row]].KeyCode()
                ])
            else:
                twi = QTableWidgetItem(
                    str(self.stack.base['s'][self.order[row]].DateEnd())
                )

        if col == 4:
            txt = self.ui.tableWidget_meas.item(row, col).text()
            self.stack.base['s'][self.order[row]].set_meta('SapWood', int(txt))
        if col == 5:
            txt = self.ui.tableWidget_meas.item(row, col).text()
            self.stack.base['s'][self.order[row]].set_meta('Bark', txt)

        if twi is not False:
            self.ui.tableWidget_meas.blockSignals(True)
            self.ui.tableWidget_meas.setItem(row, col, twi)
            self.ui.tableWidget_meas.blockSignals(False)
        else:
            self.redraw_chart()

    def sync_db_to_twmeas(self, rows=[]):
        '''called when something was changed in sample (added new meas) and it
        should be shown to user. Updates tw_meas all samples and redraws chart.
        rows - list with names of samples to refresh from db, if empty ref. all
        '''
        self.ui.tableWidget_meas.blockSignals(True)
        st = self.stack.base['s']
        if len(rows) == 0:
            rows = self.order
        for i, smp in enumerate(rows):
            twi = QTableWidgetItem(str(st[smp].DateBegin()))
            self.ui.tableWidget_meas.setItem(self.order.index(smp), 1, twi)
            twi = QTableWidgetItem(str(st[smp].DateEnd()))
            self.ui.tableWidget_meas.setItem(self.order.index(smp), 2, twi)
            twi = QTableWidgetItem(str(st[smp].Length()))
            twi.setFlags(Qt.ItemIsEditable | Qt.ItemIsSelectable)
            self.ui.tableWidget_meas.setItem(self.order.index(smp), 3, twi)
            twi = QTableWidgetItem(str(st[smp].export_meta('SapWood')))
            self.ui.tableWidget_meas.setItem(self.order.index(smp), 4, twi)

        self.ui.tableWidget_meas.blockSignals(False)
        self.redraw_chart()

    def keyPressEvent(self, e):
        key = e.key()

        if key == Qt.Key_Space:
            self.read_measure()

        if str(key) == str(Qt.Key_F3):
            sel, rows = self.selected_twmeas_rows()
            for row in rows:
                seq = self.stack.base['s'][self.order[row]]
                seq.setDateBegin(seq.DateBegin()-1)
            self.sync_db_to_twmeas()

        if str(key) == str(Qt.Key_F4):
            sel, rows = self.selected_twmeas_rows()
            for row in rows:
                seq = self.stack.base['s'][self.order[row]]
                seq.setDateBegin(seq.DateBegin()+1)
            self.sync_db_to_twmeas()

        if str(key) == str(Qt.Key_Up):
            self.offset += 1

        if str(key) == str(Qt.Key_Down):
            if self.offset > 0:
                self.offset -= 1
