from PyQt5.QtWidgets import QMessageBox, QWidget


class UserDecorators:
    def should_be_closed(meth):
        def wrap(self):
            if not self.opened:
                meth(self)
            else:
                msgBox = QMessageBox()
                msgBox.setText(
                    'Please end measuring session of current sequence'
                )
                msgBox.exec_()
        return wrap

    def should_be_opened(meth):
        def wrap(self):
            if self.opened:
                meth(self)
            else:
                msgBox = QMessageBox()
                msgBox.setText(
                    'Firstly, start new sequence from Measurements panel'
                )
                msgBox.exec_()
        return wrap

    # decorator to select measure button after clicked something else
    def select_measure_button(meth):
        def wrap(self):
            meth(self)
            QWidget.setFocus(self.ui.pushButton_read_measure)
        return wrap
