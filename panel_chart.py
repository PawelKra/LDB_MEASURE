from PyQt6.QtWidgets import QMenu, QInputDialog
from PyQt6.QtGui import QCursor, QAction
import matplotlib
import classes


class PanelChart:
    # how many ring-edit steps the undo / redo stacks keep
    _UNDO_LIMIT = 50

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
            smpl = self.stack.get('s', name)
            if smpl is None:
                continue

            yrs = smpl.years()              # calendar years, never contains 0
            chdata.append([
                yrs,
                [x+i*100 for x in smpl.measurements()],
            ])

            if smpl.SapWood() > 0:
                # bold only the last `SapWood` rings (a ring count), clamped
                # so it never runs past the start of the curve
                sw = min(smpl.SapWood(), smpl.Length())
                sapdata.append([
                    yrs[-sw:],
                    [x+i*100 for x in smpl.measurements()[-sw:]],
                ])

            min_year.append(smpl.DateBegin())
            max_year.append(smpl.DateEnd())

        # calculate int values
        min_year = min(min_year) - 1 if len(min_year) > 0 else 0
        max_year = max(max_year) + 8 if len(max_year) > 0 else 70

        # stop here if there is no data to draw
        if 0 in [len(x[1]) for x in chdata]:
            return

        for tab in sapdata:
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
        # year 0 does not exist on a calendar axis - never label a tick "0"
        self.ui.widget.canvas.ax.get_xaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(
                lambda v, pos: '' if round(v) == 0 else format(int(round(v)),
                                                               'd')))
        self.ui.widget.canvas.ax.grid(axis='x', which='both')
        self.ui.widget.canvas.ax.grid(axis='x', which='minor', linewidth=0.2)
        self.ui.widget.canvas.ax.set_position([0.001, 0.07, 0.99, 0.91])

        # show statistics if one sample is selected in stack of measures
        if selected == 1 and len(self.order) > 1:
            ref = str(self.ui.tableWidget_meas.item(selrows[0], 0).text())
            corel = 'KEY   CC    TBP   TH    T     GLK   GLS   CDI'
            ref_seq = self.stack.get('s', ref)
            for name in self.order:
                if name == ref:
                    continue
                smpl_seq = self.stack.get('s', name)
                if smpl_seq is None or ref_seq is None:
                    continue
                corel += '\n' + ''.join(map(
                    classes.format_text_spaces,
                    [name] + classes.corellate_position(smpl_seq, ref_seq)))

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

        undo_stack, redo_stack = self._edit_history()
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

        self.menu.addSeparator()
        undoAction = QAction('Undo ring edit', self)
        undoAction.setEnabled(bool(undo_stack))
        undoAction.triggered.connect(self.undo_edit)
        redoAction = QAction('Redo ring edit', self)
        redoAction.setEnabled(bool(redo_stack))
        redoAction.triggered.connect(self.redo_edit)
        self.menu.addAction(undoAction)
        self.menu.addAction(redoAction)

        self.menu.popup(QCursor.pos())

    # --- ring-edit undo / redo -------------------------------------------

    def _edit_history(self):
        '''(undo_stack, redo_stack) for ring edits, created on first use.

        new_sample() clears both so snapshots never outlive the samples they
        point at.
        '''
        if not hasattr(self, '_undo_stack'):
            self._undo_stack = []
            self._redo_stack = []
        return self._undo_stack, self._redo_stack

    def _snapshot(self, name):
        '''State of one sample that a ring edit can change, or None if the
        sample is gone.'''
        smp = self.stack.get('s', name)
        if smp is None:
            return None
        return {
            'name': name,
            'measurements': list(smp.measurements()),
            'DateBegin': smp.DateBegin(),
        }

    def _record_edit(self, before):
        '''Push a pre-edit snapshot onto the undo stack and drop the redo
        stack. Call only once an edit has actually changed the sample.'''
        undo_stack, redo_stack = self._edit_history()
        undo_stack.append(before)
        del undo_stack[:-self._UNDO_LIMIT]     # keep it bounded
        redo_stack.clear()

    def _restore(self, snap):
        smp = self.stack.get('s', snap['name'])
        if smp is None:
            return False
        smp.update_measurements(list(snap['measurements']))
        smp.setDateBegin(snap['DateBegin'])
        self.saved = False
        self.sync_db_to_twmeas()
        return True

    def undo_edit(self):
        undo_stack, redo_stack = self._edit_history()
        if not undo_stack:
            self.ui.statusbar.showMessage('Nothing to undo')
            return
        snap = undo_stack.pop()
        current = self._snapshot(snap['name'])
        if current is None or not self._restore(snap):
            self.ui.statusbar.showMessage(
                'Cannot undo: sample %s is gone' % snap['name'])
            return
        redo_stack.append(current)
        self.ui.statusbar.showMessage('Undid ring edit on ' + snap['name'])

    def redo_edit(self):
        undo_stack, redo_stack = self._edit_history()
        if not redo_stack:
            self.ui.statusbar.showMessage('Nothing to redo')
            return
        snap = redo_stack.pop()
        current = self._snapshot(snap['name'])
        if current is None or not self._restore(snap):
            self.ui.statusbar.showMessage(
                'Cannot redo: sample %s is gone' % snap['name'])
            return
        undo_stack.append(current)
        self.ui.statusbar.showMessage('Redid ring edit on ' + snap['name'])

    def _edit_ring(self, event, mutate, verb):
        '''Run ``mutate(smp)`` on the one selected sample; if it changed the
        ring list, record an undo snapshot and refresh the UI.'''
        sel, rows = self.selected_twmeas_rows()
        if sel != 1:
            return

        name = self.order[rows[0]]
        before = self._snapshot(name)
        if before is None:
            return
        smp = self.stack.get('s', name)
        mutate(smp)
        if list(smp.measurements()) == before['measurements']:
            return                             # year out of range / no change
        self._record_edit(before)
        self.saved = False
        self.sync_db_to_twmeas()
        self.ui.statusbar.showMessage(
            '%s increment in %s (at year %d)'
            % (verb, name, int(round(event.xdata))))

    def delete_slot(self, event):
        year = int(round(event.xdata, 0))
        self._edit_ring(
            event, lambda smp: smp.delete_year_measurement(year), 'Deleted')

    def add_slot(self, event):
        sel, rows = self.selected_twmeas_rows()
        if sel != 1:
            return

        smp = self.stack.get('s', self.order[rows[0]])
        if smp is None:
            return
        year = int(round(event.xdata, 0))
        val = smp.measure_from_year(year)
        val, ok = QInputDialog.getInt(
            self, 'Add value in year', 'Value in micrometers (mm*100):',
            value=val, min=1, max=99999, step=1)
        if ok and int(val) > 0:
            self._edit_ring(
                event,
                lambda smp: smp.add_year_measurement(year, val), 'Added')

    def change_slot(self, event):
        sel, rows = self.selected_twmeas_rows()
        if sel != 1:
            return

        smp = self.stack.get('s', self.order[rows[0]])
        if smp is None:
            return
        year = int(round(event.xdata, 0))
        val = smp.measure_from_year(year)
        val, ok = QInputDialog.getInt(
            self, 'Change increment', 'Value in micrometers (mm*100):',
            value=val, min=1, max=99999, step=1)
        if ok and int(val) > 0:
            self._edit_ring(
                event,
                lambda smp: smp.update_year_measurement(year, int(val)),
                'Changed')

    def onMouseMove(self, event):
        if event.xdata is None:
            return
        if int(event.xdata) != self.line_x:
            self.line_x = int(event.xdata)
            self.line.set_xdata([event.xdata, event.xdata])
            self.ui.widget.canvas.draw()
