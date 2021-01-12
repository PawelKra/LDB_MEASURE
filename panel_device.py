from user_decorators import UserDecorators
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QTextCursor
import classes


class PanelDevice:
    @UserDecorators.should_be_opened
    def read_measure(self):
        '''read current counter state and calculate current measure accordingly
           taking impulses/mm, insert into textEdit_meas value of measurement
        '''
        meas = self.dev.read_measurement()
        if meas > 0:
            self.opened.add_measurement(meas)
            self.update_textedit_meas()
            self.sync_db_to_twmeas()

    @UserDecorators.should_be_opened
    @UserDecorators.select_measure_button
    def set_sapwood(self):
        '''write into lineEdit_sapwood, current ring number
        '''
        if len(self.opened.measurements()) > 0:
            self.ui.lineEdit_sapwood.setText(str(self.opened.Length()))

    @UserDecorators.should_be_opened
    @UserDecorators.select_measure_button
    def delete_last_measure(self):
        '''deletes last measure from current sequence, redraw textEdit_meas
        '''
        self.opened.measurements().pop()
        self.update_textedit_meas()
        self.sync_db_to_twmeas()

    @UserDecorators.should_be_opened
    def end_sequence(self):
        '''ends measuring session, set opened to false
        '''
        if self.ui.lineEdit_sapwood.text() != '':
            self.opened.set_meta('SapWood',
                                 int(self.ui.lineEdit_sapwood.text()))
        self.opened = False
        self.clear_device_panel()

    @UserDecorators.should_be_opened
    @UserDecorators.select_measure_button
    def clean(self):
        '''cleans all data from current measure sessions, delete all measures,
        set counter to 0
        '''
        self.dev.set_zeros()
        self.opened.update_measurements([])
        self.clear_device_panel()
        self.sync_db_to_twmeas()

    def clear_device_panel(self):
        '''Sets defaluts values to device panel, sets it ready to use, after
        every measure
        '''
        self.ui.textEdit_meas.setText('')
        self.ui.lineEdit_sapwood.setText('')

    def update_textedit_meas(self):
        max_len = len(str(len(self.opened.measurements())))
        out = '\n'.join(
            [classes.format_text_spaces(i+1, text_len=max_len)+'  ' +
             str(x/100)+(2-len(str(x/100).split('.')[-1]))*'0'
             for i, x in enumerate(self.opened.measurements())]
        )
        self.ui.textEdit_meas.setText(out)
        self.ui.textEdit_meas.moveCursor(QTextCursor.End)

    def setup_device(self):
        # check if we have attached any device on port
        if not self.testrun:
            if self.dev.status == 0:
                msgBox = QMessageBox()
                msgBox.setText('NO DEVICE FOUND!\n'
                               '(Please check if COM port didn\'t changed)\n'
                               '(Please check cables)'
                               )
                msgBox.exec_()
                return False
            else:
                self.dev.set_zeros()
        return True
