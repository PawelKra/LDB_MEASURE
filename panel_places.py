import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox


class PanelPlaces:
    def choose_dir(self):
        '''choose existing dir from disk to store means in it, update
        lineEdit_cat_means, and asks question to user if there should be
        created /R catalog in in to store measured sequences.
        '''
        d = QFileDialog()
        b = self.setts.def_cat
        dir_m = d.getExistingDirectory(
            self, 'Choose directory:', b, QFileDialog.ShowDirsOnly
        )
        if dir_m in ['', None, 'None', 'NULL', '/']:
            return
        self.ui.lineEdit_cat_means.setText(dir_m)

        answ = QMessageBox.question(
            self, "Set sample dir",
            'Create/set R catalog in Mean path?',
            QMessageBox.Yes, QMessageBox.No)
        if answ == QMessageBox.Yes:
            dir_r = os.path.join(dir_m, 'R')
            if not os.path.exists(dir_r):
                os.makedirs(dir_r)
            self.ui.lineEdit_cat_samples.setText(dir_r)
        else:
            self.ui.lineEdit_cat_samples.setText(dir_m)

        self.ui.statusbar.showMessage('Setup dirs for work')
