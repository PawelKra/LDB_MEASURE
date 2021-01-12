from PyQt5.QtWidgets import QDialog
from ui_LDB_Ccoptions import Ui_DialogOpt


class Options(QDialog):
    def __init__(self):
        super(QDialog, self).__init__()
        self.ui = Ui_DialogOpt()
        self.ui.setupUi(self)
        self.cancel = True

        self.ui.pushButton_cancel.clicked.connect(self.cancelm)
        self.ui.pushButton_ok.clicked.connect(self.ok)

    def cancelm(self):
        self.hide()

    def ok(self):
        self.cancel = False
        self.hide()
