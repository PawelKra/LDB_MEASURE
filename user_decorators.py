from PyQt6.QtWidgets import QMessageBox, QWidget


class UserDecorators:
    def should_be_closed(meth):
        def wrap(self):
            if not self.opened:
                return meth(self)
            msgBox = QMessageBox()
            msgBox.setText(
                'Please end measuring session of current sequence'
            )
            msgBox.exec()
        return wrap

    def should_be_opened(meth):
        def wrap(self):
            if self.opened:
                return meth(self)
            msgBox = QMessageBox()
            msgBox.setText(
                'Firstly, start new sequence from Measurements panel'
            )
            msgBox.exec()
        return wrap

    # decorator to select measure button after clicked something else
    def select_measure_button(meth):
        def wrap(self):
            result = meth(self)
            QWidget.setFocus(self.ui.pushButton_read_measure)
            return result
        return wrap
