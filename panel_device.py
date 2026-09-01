from user_decorators import UserDecorators
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QTextCursor
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
        '''Mark the current ring as the first sapwood ring. The number shown
        is that ring's position; end_sequence converts it to the sapwood
        ring *count* that gets stored in the SapWood metadata.
        '''
        if len(self.opened.measurements()) > 0:
            self.sapwood_beg = self.opened.Length()
            self.ui.lineEdit_sapwood.setText(str(self.sapwood_beg))

    @UserDecorators.should_be_opened
    @UserDecorators.select_measure_button
    def delete_last_measure(self):
        '''deletes last measure from current sequence, redraw textEdit_meas
        '''
        if not self.opened.measurements():
            return
        self.opened.measurements().pop()
        self.update_textedit_meas()
        self.sync_db_to_twmeas()

    @UserDecorators.should_be_opened
    def end_sequence(self):
        '''ends measuring session, set opened to false
        '''
        seq = self.opened
        txt = self.ui.lineEdit_sapwood.text()
        if self.sapwood_beg > 0 and txt.isdigit():
            # field holds the first-sapwood-ring number: store the ring count
            beg = int(txt)
            seq.set_meta('SapWood', max(0, seq.Length() - beg + 1))
        elif txt.isdigit():
            # typed straight in: already a sapwood ring count
            seq.set_meta('SapWood', int(txt))
        self.sapwood_beg = 0
        self.opened = False
        self.clear_device_panel()
        # surface the freshly stored SapWood count in the measurements table
        # (and redraw the chart). save_sample re-reads column 4 from that
        # table, so without this the value is lost on the next save.
        self.sync_db_to_twmeas([seq.KeyCode()])

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
        self.ui.textEdit_meas.moveCursor(QTextCursor.MoveOperation.End)

    def setup_device(self):
        # check if we have attached any device on port
        if not self.testrun:
            if self.dev.status == 0:
                msgBox = QMessageBox()
                msgBox.setText('NO DEVICE FOUND!\n'
                               '(Please check if COM port didn\'t changed)\n'
                               '(Please check cables)'
                               )
                msgBox.exec()
                return False
            else:
                self.dev.set_zeros()
        return True
