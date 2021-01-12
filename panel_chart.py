from PyQt5.QtWidgets import QMenu, QInputDialog, QAction
from PyQt5.QtGui import QCursor
import matplotlib
import classes


class PanelChart:
    def redraw_chart(self):
        '''redraw chart on data derived from database
        '''
        self.ui.widget.canvas.ax.clear()  # clean widet
        selected, selrows = self.selected_twmeas_rows()
        self.line_x = 0

        chdata = []  # list with data for every smpl to put on chart
        # important to know how many years we want to draw because mpl has
        # limitation of showing year ticks, to many and it will crash
        min_year = []  # min year on chart
        max_year = []  # max year on chart

        sapdata = []  # list with SapWood data do draw on chart
        for i, name in enumerate(self.order):
            smpl = list(self.stack.seq_from_stack('s', [name]).values())[0]

            chdata.append([
                [y for y in range(smpl.DateBegin(), smpl.DateEnd()+1)],
                [x+i*100 for x in smpl.measurements()],
            ])

            if smpl.SapWood() > 0:
                sapdata.append([
                    [y for y in range(smpl.DateEnd()-smpl.SapWood(),
                                      smpl.DateEnd()+1)],
                    [smpl.measure_from_year(x)+i*100
                     for x in range(smpl.DateEnd()-smpl.SapWood(),
                                    smpl.DateEnd()+1)]
                ])

            min_year.append(smpl.DateBegin())
            max_year.append(smpl.DateEnd())

        # calculate int values
        min_year = min(min_year) - 1 if len(min_year) > 0 else 0
        max_year = max(max_year) + 8 if len(max_year) > 0 else 70

        # stop here if there is no data to draw
        if 0 in [len(x[1]) for x in chdata]:
            return

        for i, tab in enumerate(sapdata):
            lwd = 1 if i not in selrows else 2
            self.ui.widget.canvas.ax.plot(*tab, linewidth=4, color='gray')

        for i, tab in enumerate(chdata):
            lwd = 1 if i not in selrows else 2
            self.ui.widget.canvas.ax.plot(*tab, linewidth=lwd)
            self.ui.widget.canvas.ax.text(
                max(tab[0])+1, tab[1][-1], self.order[i])

        self.ui.widget.canvas.ax.get_yaxis().set_visible(False)
        self.ui.widget.canvas.ax.set_xlim(min_year, max_year)
        locator = 5 if (max_year-min_year) < 999 else 25
        self.ui.widget.canvas.ax.get_xaxis().set_minor_locator(
            matplotlib.ticker.MultipleLocator(locator))
        self.ui.widget.canvas.ax.grid(axis='x', which='both')
        self.ui.widget.canvas.ax.grid(axis='x', which='minor', linewidth=0.2)
        self.ui.widget.canvas.ax.set_position([0.001, 0.07, 0.99, 0.91])

        # show statistics if one sample is selected in stack of measures
        if selected == 1 and len(self.order) > 1:
            ref = str(self.ui.tableWidget_meas.item(selrows[0], 0).text())
            corel = 'KEY   CC    TBP   TH    T     GLK   GLS   CDI'
            for name in self.order:
                if name == ref:
                    continue
                corel += '\n' + ''.join(map(
                    classes.format_text_spaces,
                    [name] + classes.corellate_position(
                        self.stack.seq_from_stack('s', [name])[name],
                        self.stack.seq_from_stack('s', [ref])[ref],
                    )))

            bbox_p = dict(boxstyle='square', fc='w', ec='0.5', alpha=0.7)
            self.ui.widget.canvas.ax.text(
                0.65, 0.97,
                corel,
                fontsize=8,
                bbox=bbox_p,
                verticalalignment='top',
                horizontalalignment='left',
                fontdict={'fontfamily': 'monospace'},
                transform=self.ui.widget.canvas.ax.transAxes,
            )

        self.line = self.ui.widget.canvas.ax.axvline(x=0., color='k')

        self.ui.widget.canvas.draw()

    def mouseClick(self, event):
        if event.button != 3:
            return

        selrows, others = self.selected_twmeas_rows()
        self.menu = QMenu(self)
        if selrows != 1:
            remiderAction = QAction(
                'Select just/only one sample to edit!', self
            )
            self.menu.addAction(remiderAction)
        else:
            deleteAction = QAction('Delete', self)
            deleteAction.triggered.connect(lambda: self.delete_slot(event))
            changeAction = QAction('Modify', self)
            changeAction.triggered.connect(lambda: self.change_slot(event))
            addAction = QAction('Add', self)
            addAction.triggered.connect(lambda: self.add_slot(event))
            self.menu.addAction(deleteAction)
            self.menu.addAction(addAction)
            self.menu.addAction(changeAction)

        self.menu.popup(QCursor.pos())

    def delete_slot(self, event):
        sel, rows = self.selected_twmeas_rows()
        if sel != 1:
            return

        smp = self.stack.base['s'][self.order[rows[0]]]
        smp.delete_year_measurement(int(round(event.xdata, 0)))
        self.saved = False
        self.sync_db_to_twmeas()
        self.ui.statusbar.showMessage(
            'Deleted increment from '+smp.KeyCode() +
            '(at year '+str(int(round(event.xdata)))+')')

    def add_slot(self, event):
        sel, rows = self.selected_twmeas_rows()
        if sel != 1:
            return

        smp = self.stack.base['s'][self.order[rows[0]]]
        val = smp.measure_from_year(int(round(event.xdata, 0)))
        val, ok = QInputDialog.getInt(
            self, 'Add value in year', 'Value in micrometers (mm*100):',
            value=val, min=1, max=99999, step=1)
        if ok and int(val) > 0:
            smp = self.stack.base['s'][self.order[rows[0]]]
            smp.add_year_measurement(int(round(event.xdata, 0)), val)
            self.saved = False
            self.sync_db_to_twmeas()
            self.ui.statusbar.showMessage(
                'Added increment to '+smp.KeyCode() +
                '(at year '+str(int(round(event.xdata)))+')')

    def change_slot(self, event):
        sel, rows = self.selected_twmeas_rows()
        if sel != 1:
            return

        smp = self.stack.base['s'][self.order[rows[0]]]
        val = smp.measure_from_year(int(round(event.xdata, 0)))
        val, ok = QInputDialog.getInt(
            self, 'Change increment', 'Value in micrometers (mm*100):',
            value=val, min=1, max=99999, step=1)
        if ok and int(val) > 0:
            smp.update_year_measurement(
                int(round(event.xdata, 0)), int(val)
            )
            self.saved = False
            self.sync_db_to_twmeas()
            self.ui.statusbar.showMessage(
                'Changed increment in '+smp.KeyCode() +
                '(at year '+str(int(round(event.xdata)))+')')

    def onMouseMove(self, event):
        if event.xdata is None:
            return
        if int(event.xdata) != self.line_x:
            self.line_x = int(event.xdata)
            self.line.set_xdata([event.xdata, event.xdata])
            self.ui.widget.canvas.draw()
