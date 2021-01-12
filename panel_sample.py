import os
from user_decorators import UserDecorators
from PyQt5.QtWidgets import QTableWidgetItem, QWidget, QFileDialog, \
    QMessageBox, QTableWidget

import classes


class PanelSample:
    @UserDecorators.should_be_closed
    def new_sample(self):
        '''Clearing all data and sets program to process new sample.
        if previous sample is not set to saved, it asks user for saving
        unsaved
        data.
        '''
        if not self.saved:
            ret = QMessageBox.question(
                self, 'Write sample',
                'Save current measures?',
                QMessageBox.Yes, QMessageBox.No
            )
            if ret == QMessageBox.Yes:
                ok = self.save_sample()
                if not ok:
                    return

        self.reset_tW_attr()
        self.reset_tW_meas()

        self.show_stats = False
        self.stack.clear()
        self.order = []
        self.saved = True

        QWidget.setFocus(self.ui.pushButton_new_sequence)
        self.redraw_chart()
        self.ui.statusbar.showMessage(
            'New sample created, ready for measurements'
        )

    def reset_tW_attr(self):
        '''resets tableWidget_attr to default values of header from sett class
        readed from settings file
        '''
        self.ui.tableWidget_attr.clear()
        self.ui.tableWidget_attr.setColumnCount(1)
        self.ui.tableWidget_attr.setRowCount(len(self.setts.headers))
        self.ui.tableWidget_attr.setHorizontalHeaderLabels(['Value'])
        self.ui.tableWidget_attr.setVerticalHeaderLabels(self.setts.headers)
        self.ui.tableWidget_attr.setAlternatingRowColors(True)
        self.ui.tableWidget_attr.setSortingEnabled(False)

        for i, key in enumerate(self.setts.headers):
            if key in ['DateBegin', 'DateEnd', ]:
                t1 = 't'
            elif key == 'KeyCode':
                t1 = '---'
            else:
                t1 = ''
            cell = QTableWidgetItem(t1)
            self.ui.tableWidget_attr.setItem(i, 0, cell)

    def reset_tW_meas(self):
        sd = self.ui.tableWidget_meas
        sd.blockSignals(True)
        sd.setColumnCount(8)
        sd.setRowCount(0)
        sd.setHorizontalHeaderLabels(self.setts.def_sample_headers)
        sd.setAlternatingRowColors(True)
        sd.setSortingEnabled(False)
        sd.resizeColumnsToContents()
        sd.setSelectionBehavior(QTableWidget.SelectRows)
        sd.blockSignals(False)

    @UserDecorators.should_be_closed
    def save_sample(self):  # noqa
        '''Saves current sequences and means with attributes to adequate
        catalogs
        '''
        if str(self.ui.tableWidget_attr.item(0, 0).text()) == '---':
            msgBox = QMessageBox()
            msgBox.setText('Set proper name for sample! (KeyCode)')
            msgBox.exec_()
            return False

        # create list or R and M sequences
        Mlist = [x for x in self.order if x[0] == 'M']

        # dicts of Sequence obj with all attrs to save to file
        mdict = {}
        rdict = {}

        # universal dict with all attrs
        univ = {}
        for j in range(self.ui.tableWidget_attr.rowCount()):
            val = str(self.ui.tableWidget_attr.item(j, 0).text())
            if val != '':
                univ[self.setts.headers[j]] = val
        mname = univ['KeyCode']

        for i in range(len(self.order)):
            stmp = classes.Sequence(univ)
            for j in range(4, len(self.setts.def_sample_headers)):
                rv = str(self.ui.tableWidget_meas.item(i, j).text())
                if j == 4:
                    # set DateBegin
                    dbeg = str(self.ui.tableWidget_meas.item(i, 1).text())
                    stmp.setDateBegin(dbeg)
                    # set proper KeyCode
                    kc = str(self.ui.tableWidget_meas.item(i, 0).text())
                    stmp.update_measurements(
                        list(
                            self.stack.seq_from_stack('s', [kc]).values()
                        )[0].measurements())
                    adds = '_' + kc
                    if len(Mlist) > 0:
                        if kc == Mlist[0]:
                            adds = ''
                    stmp.set_meta('KeyCode', mname+adds)
                    if rv != '':
                        stmp.set_meta('SapWood', int(rv))
                if rv != '':
                    if j == 5:
                        stmp.set_meta('pith_growth', int(rv))
                    if j > 5:
                        stmp.set_meta(self.setts.def_sample_headers[j], rv)

            if self.order[i][0] == 'R':
                rdict[stmp.KeyCode()] = stmp
            else:
                mdict[stmp.KeyCode()] = stmp

        # generate path to new files, check if exiests
        ext = str(self.ui.comboBox_format.currentText())[1:]
        cat_smpl = str(self.ui.lineEdit_cat_samples.text())
        cat_means = str(self.ui.lineEdit_cat_means.text())

        if ext in ['.txt', '.avr']:
            rpaths = [os.path.join(cat_smpl, x+ext) for x in rdict.keys()]
            mpaths = [os.path.join(cat_means, x+ext) for x in mdict.keys()]
        else:
            rpaths = [os.path.join(cat_smpl, mname+'_R'+ext)]
            mpaths = [os.path.join(cat_means, mname+ext)]

        if True in list(map(os.path.exists, rpaths+mpaths)):
            ret = QMessageBox.question(
                self, 'Overwrite samples',
                'Overwrite measures?',
                QMessageBox.Yes, QMessageBox.No
            )
            if ret == QMessageBox.No:
                return False

        if ext == '.fh':
            classes.write_fh(rpaths[0], rdict)
            classes.write_fh(mpaths[0], mdict)
        elif ext == '.txt':
            for it in mdict.values():
                classes.write_txt(
                    os.path.join(cat_means, it.KeyCode()+ext), it
                )
            for it in rdict.values():
                classes.write_txt(
                    os.path.join(cat_smpl, it.KeyCode()+ext), it
                )
        elif ext == '.avr':
            for it in mdict.values():
                classes.write_r(
                    os.path.join(cat_means, it.KeyCode()+ext), it
                )
            for it in rdict.values():
                classes.write_r(
                    os.path.join(cat_smpl, it.KeyCode()+ext), it
                )

        self.saved = True

        self.ui.statusbar.showMessage('Sample saved')
        # if in testing skip showing measseages
        if len(self.test_samples) > 0:
            return True

        msgBox = QMessageBox()
        msgBox.setText("Saved: "+str(len(mdict.keys()))+' means, ' +
                       str(len(rdict.keys()))+' samples;'
                       )
        msgBox.exec_()
        return True

    @UserDecorators.should_be_closed
    def load_samples(self):
        '''Load samples from disk to stack'''
        if len(self.test_samples) == 0:
            dial = QFileDialog()
            paths, filters = dial.getOpenFileNames(
                self,
                'Open Files',
                self.setts.def_cat,
                'Supported (*.fh *.av* *.pos *.rwl)'
            )
        else:
            paths = self.test_samples

        # dict with Sequence files, readed from file
        samps = {}
        # list for paths with fh files, packing it in list will provide us
        # checking on duplicates
        fh_files = []
        for pth in paths:
            path = str(pth)
            cat, nm = os.path.split(path)
            name, ext = nm.split('.')
            if ext.upper() == 'FH':
                fh_files.append(path)
            elif ext.upper() == 'RWL':
                samps.update(classes.read_rwl(path))
            elif ext.upper()[:2] == 'AV':
                samps.update(classes.read_r(path))
            elif ext.upper() == 'POS':
                samps.update(classes.read_pos(path))

        if len(fh_files) > 0:
            samps.update(classes.read_fh(fh_files))

        if len(samps) > 20:
            msgBox = QMessageBox()
            msgBox.setText('You can open only 20 samples')
            msgBox.exec_()
            return

        for val in samps.values():
            self.add_meas_to_tWMeas(val)

        self.saved = False
        self.ui.statusbar.showMessage(
            'Loaded '+str(len(samps.keys()))+' samples'
        )
