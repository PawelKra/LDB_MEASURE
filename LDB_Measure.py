import sys
from PyQt5.QtWidgets import QMainWindow, QApplication

from ui_LDB_Measure import Ui_MainWindow
import classes
from config import ReadConfig
from devices import Device
from user_decorators import UserDecorators
from panel_sample import PanelSample
from panel_places import PanelPlaces
from panel_attributes import PanelAttributes
from panel_measurements import PanelMeasurements
from panel_device import PanelDevice
from panel_chart import PanelChart
from sett_window import SettWindow


class LDB_Form(QMainWindow,
               UserDecorators,
               PanelSample,
               PanelPlaces,
               PanelAttributes,
               PanelMeasurements,
               PanelDevice,
               PanelChart,
               ):

    def __init__(self):
        super(QMainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # init simple database to store Sequence objects
        self.stack = classes.DataBase('s')
        # show stats of selected sample to others on chart
        self.show_stats = False
        # check if device is up, running and we can connect to it
        self.connected = False
        # trigger for knowing if device is open and user is measuring sample
        # if False all device panel is disabled
        self.opened = False
        # is current sample is saved, and when close program, loose data
        self.saved = True
        # setting readed from file
        self.setts = ReadConfig('settings.txt')
        # list with order of samples in tableWidget_measures
        self.order = []
        # list with path to test case sample files
        self.test_samples = []  # using only on testing
        self.testrun = False  # trigger for testing, exceptions are ommited
        # offset to add to sample measurements to avoid crossing on chart
        self.offset = 1
        # set default catalogs for start
        self.ui.lineEdit_cat_means.setText(self.setts.def_cat)
        self.ui.lineEdit_cat_samples.setText(self.setts.def_cat)

        # setup counter device
        self.dev = Device(self.setts)

        self.ui.pushButton_new_sample.clicked.connect(self.new_sample)
        self.ui.pushButton_load_sample.clicked.connect(self.load_samples)
        self.ui.pushButton_save_sample.clicked.connect(self.save_sample)
        self.ui.tableWidget_meas.itemSelectionChanged.connect(
                                                self.redraw_chart)
        self.ui.pushButton_choose_dir.clicked.connect(self.choose_dir)
        self.ui.pushButton_settings.clicked.connect(self.show_settings)

        self.ui.pushButton_new_sequence.clicked.connect(self.new_sequence)
        self.ui.pushButton_continue_sequence.clicked.connect(
                                                self.continue_sequence)
        self.ui.pushButton_delete_sequence.clicked.connect(
                                                self.delete_sequences)
        self.ui.pushButton_cor_selected.clicked.connect(
                                                self.correlate_sequences)
        self.ui.pushButton_mean_selected.clicked.connect(self.create_mean)
        self.ui.pushButton_read_measure.clicked.connect(self.read_measure)
        self.ui.pushButton_sapwood_beg.clicked.connect(self.set_sapwood)
        self.ui.pushButton_delete_measure.clicked.connect(
                                                self.delete_last_measure)
        self.ui.pushButton_end_measures.clicked.connect(self.end_sequence)
        self.ui.pushButton_clean.clicked.connect(self.clean)

        self.ui.tableWidget_meas.cellChanged.connect(self.sync_twmeas_to_db)
        self.ui.widget.canvas.mpl_connect(
                                        'button_press_event', self.mouseClick)
        self.ui.widget.canvas.mpl_connect(
            'motion_notify_event', self.onMouseMove)

        # initialize all structures and set program ready to go
        self.new_sample()
        self.ui.statusbar.showMessage('Ready to work!')

    def clear_forms(self):
        '''Clear all forms in MainWindows and sets all for new sample
        '''

    @UserDecorators.should_be_closed
    def show_settings(self):
        '''Show setting window where user can edit default dir, choose
        counter device, and set impulse/mm acordingly. There is also option
        to set headers for fh attributes if there is need to put some attribs
        in this file. Attributes can be saved only in fh file, other formats
        dont support metadata
        '''
        settwnd = SettWindow(self.setts)
        settwnd.exec_()
        # set new defaults if user made chages
        if settwnd.overwritten:
            self.ui.lineEdit_cat_means.setText(self.setts.def_cat)
            self.ui.lineEdit_cat_samples.setText(self.setts.def_cat)
            self.new_sample()
            self.ui.statusbar.showMessage('New settings deployed!')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = LDB_Form()
    form.show()
    app.exec_()
    sys.exit(0)
