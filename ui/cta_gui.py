from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
from epics import PV
import numpy
import argparse
from enum import Enum
import logging

class SequenceState(Enum):
    EQUAL = 1
    UNEQUAL = 2
    UNKNOWN = 3

class SequenceTableModel(QAbstractTableModel):
    
    def __init__(self, parent, serMaxLen, sequence = [[]], headers = [], localEvents = []):
        QAbstractTableModel.__init__(self, parent)
        self.__parent = parent
        self.__sequence = sequence
        self.__headers = headers
        self.__columnMap = {'stepOff': 0, 'startOff': 1, 'evtCode': 2}
        self.__localEvents = localEvents
        self.__serMaxLen = serMaxLen

    def rowCount(self, parent):
        return len(self.__sequence)
    
    def columnCount(self, parent):
        return len(self.__columnMap)

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):
        
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            return self.__sequence[row][column]
        
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            value = self.__sequence[row][column]
            
            return value

    # This method is called by the view if the user entered new data
    #
    # index: index at which to change the data
    # value: new value for the data        
    # role : edit role
    def setData(self, index, value, role = Qt.EditRole):

        row = index.row()
        column = index.column()
        
        if column == self.__columnMap['evtCode']:
            rc, uIndTopLeft, uIndBotRight = self.setDataEvtCode(index, value, role)
        
        if column == self.__columnMap['stepOff']:
            rc, uIndTopLeft, uIndBotRight = self.setDataStepOff(index, value, role)
        
        if column == self.__columnMap['startOff']:
            rc, uIndTopLeft, uIndBotRight = self.setDataStartOff(index, value, role)
        
        if not rc:
            return False

        # update view
        self.dataChanged.emit(uIndTopLeft, uIndBotRight)

        self.__parent.setCompare(SequenceState.UNEQUAL)

        return True

    def setDataEvtCode(self, index, value, role):

        if role == Qt.EditRole:

            row = index.row()
            column = index.column()

            # verify value
            if not (value in self.__localEvents):
                return False, 0, 0
            
            # set value
            self.__sequence[row][column] = value

            # return index for view update
            return True, index, index

    def setDataStepOff(self, index, value, role):
        
        logging.info('setDataStepOff() is running')
        
        
        if role == Qt.EditRole:

            row = index.row()
            column = index.column()
            logging.info('row=' + str(row) + ' column=' + str(column))

            # verify value

            ## value need to be in the allowed range
            if value < 0 or value >= self.__serMaxLen:
                return False, 0, 0

            ## the sum of all step offsets may not be bigger
            ## than the maximum sequence length
            sumOff = 0
            for i in range(self.rowCount(self)):
                if i != row:
                    sumOff += self.__sequence[i][column]
            if sumOff + value >= self.__serMaxLen:
                logging.info(sumOff+value)
                return False, 0, 0
            
            # set value
            self.__sequence[row][column] = value

            # update dependent data
            self.startOffFromStepOff();

            return True, index, index
            
    def setDataStartOff(self, index, value, role):
        
        logging.info('setDataStartOff() is running')
        
        if role == Qt.EditRole:

            row = index.row()
            column = index.column()
            logging.info('row=' + str(row) + ' column=' + str(column))

            # verify value

            ## start offset value need to be in the allowed range
            if value < 0 or value >= self.__serMaxLen:
                return False, 0, 0

            ## check if row and column are in the valid range
            if row < 0 or column < 0 or column > 2:
                return False, 0, 0

            ## if it is not the first row the start offset must be
            ## equal or bigger than the start offset of the previous row
            if row > 0:
                if value < self.__sequence[row - 1][column]:
                    return False, 0, 0

            ## if it is not the last row, the start offset must be smaller
            ## than the start offset of the next row
            if row < self.rowCount(self) - 1:
                if value > self.__sequence[row + 1][column]:
                    return False, 0, 0

            # set value
            self.__sequence[row][column] = value

            # update dependent data
            self.stepOffFromStartOff();

            return True, index, index
            
    def headerData(self, section, orientation, role):
        
        if role == Qt.DisplayRole:
            
            if orientation == Qt.Horizontal:
                
                if section < len(self.__headers):
                    return self.__headers[section]
                else:
                    return "not available"
            else:
                return str(section)

    # row: row index of first row to be inserted
    #      row = 0 => prepend
    #      row = rowCount() => append
    # count: number of rows to be inserted
    def insertRows(self, row, count, parent = QModelIndex()):
        logging.info('insertRows has been called')
        logging.info('row=' + str(row) + ' count=' + str(count))

        self.beginInsertRows(parent, row, row + count - 1)
        
        # insert data
        for i in range(count):
            seq_idx_before = row + i
            logging.info('seq_idx_before=' + str(seq_idx_before))
            if seq_idx_before == 0: # empty or prepend
                self.__sequence.insert(seq_idx_before,
                  [0, 0, self.__localEvents[0]])
            else:
                self.__sequence.insert(seq_idx_before,
                  [0, self.__sequence[seq_idx_before - 1]
                  [self.__columnMap['startOff']], self.__localEvents[0]])

        logging.debug(self.__sequence)
        
        self.endInsertRows()
        
        self.__parent.setCompare(SequenceState.UNEQUAL)

        return True

    # row: index of first row to be removed
    # count: number of rows to be removed
    def removeRowsKeepStepOff(self, row, count, parent = QModelIndex()):
        logging.info('removeRowsKeepStepOff has been called')
        logging.info('row=' + str(row) + ' count=' + str(count))
        
        first = row
        last = first + count - 1

        if first < 0:
            return False
        if last >= self.rowCount(self):
            return False

        self.beginRemoveRows(parent, first, last)

        self.__sequence[first:last+1] = []
        self.startOffFromStepOff()

        logging.debug(self.__sequence)

        self.endRemoveRows()
        
        self.__parent.setCompare(SequenceState.UNEQUAL)

        return True

    # row: index of first row to be removed
    # count: number of rows to be removed
    def removeRowsKeepStartOff(self, row, count, parent = QModelIndex()):
        logging.info('removeRowsKeepStartOff has been called')
        logging.info('row=' + str(row) + ' count=' + str(count))
        
        first = row
        last = first + count - 1

        if first < 0:
            return False
        if last >= self.rowCount(self):
            return False

        self.beginRemoveRows(parent, first, last)

        self.__sequence[first:last+1] = []
        self.stepOffFromStartOff()

        logging.debug(self.__sequence)

        self.endRemoveRows()
        
        self.__parent.setCompare(SequenceState.UNEQUAL)

        return True

    def startOffFromStepOff(self):
        
        cumStepOff = 0

        for i in range(len(self.__sequence)):
            cumStepOff += self.__sequence[i][self.__columnMap['stepOff']]
            self.__sequence[i][self.__columnMap['startOff']] = cumStepOff

    def stepOffFromStartOff(self):
        
        lastOff = 0

        for i in range(len(self.__sequence)):
            currOff = self.__sequence[i][self.__columnMap['startOff']]
            self.__sequence[i][self.__columnMap['stepOff']] = currOff - lastOff
            lastOff = currOff

    def getSeries(self):

        logging.info('SequenceTableModel.getSeries() is running')
        logging.debug(self.__sequence)

        # find the length of the series
        if self.rowCount(self) == 0:
            seriesLength = 1
        else:
            seriesLength = self.__sequence[-1][self.__columnMap['startOff']] + 1

        # create series and init it with zeros
        series = [None] * len(self.__localEvents)
        for i in range(len(self.__localEvents)):
            series[i] = [0] * seriesLength

        # transform table to series
        for row in range(len(self.__sequence)):
            step_offset = self.__sequence[row][self.__columnMap['startOff']]
            event_code = self.__sequence[row][self.__columnMap['evtCode']] 
            series[self.__localEvents.index(event_code)][step_offset] = 1

        logging.debug(series)
        logging.info('SequenceTableModel.getSeries() is done')

        return series

    def setSeries(self, series):

        logging.info('SequenceTableModel.setSeries() is running')
        logging.debug(series)

        # init sequence
        s = 0
        for i in range(len(self.__localEvents)):
            s += sum(series[i])
        self.__sequence = [None] * s
        for i in range(s):
            self.__sequence[i] = [None] * 3

        # loop over series
        row = 0
        for i in range(len(series[0])):

            # loop over local events
            for k in range(len(self.__localEvents)):

                # add row if enabled
                if series[k][i]:
                    if row == 0:
                        self.__sequence[row][self.__columnMap['stepOff']] = i
                    else:
                        self.__sequence[row][self.__columnMap['stepOff']] = i - self.__sequence[row-1][self.__columnMap['startOff']]
                    self.__sequence[row][self.__columnMap['startOff']] = i
                    self.__sequence[row][self.__columnMap['evtCode']] = self.__localEvents[k]
                    row += 1
        logging.debug(self.__sequence)


class SequenceTableView(QTableView):
    
    def __init__(self, parent, model):
        super(SequenceTableView, self).__init__(parent)
        self.model = model
        self.setModel(model)

    def sizeHint(self):
        horizontal = self.horizontalHeader()
        vertical = self.verticalHeader()
        frame = self.frameWidth() * 2
        return QSize(horizontal.length() + vertical.width() + frame,
          vertical.length() *10 + horizontal.height() + frame)

    def contextMenuEvent(self, event):
      logging.info("SequenceTableView::contextMenuEvent() is running")
      
      position = event.pos()
      column = self.columnAt(position.x())
      row = self.rowAt(position.y())

      self.menu = QMenu(self)

      actionAddRow = QAction('insert row', self)
      actionAddRow.triggered.connect(lambda: self.insertRow(row))
      self.menu.addAction(actionAddRow)

      actionRmRowKeepStepOff = QAction('remove row (keep step offsets)', self)
      actionRmRowKeepStepOff.triggered.connect(lambda: self.removeRowKeepStepOff(row))
      self.menu.addAction(actionRmRowKeepStepOff)

      actionRmRowKeepStartOff = QAction('remove row (keep start offsets)', self)
      actionRmRowKeepStartOff.triggered.connect(lambda: self.removeRowKeepStartOff(row))
      self.menu.addAction(actionRmRowKeepStartOff)

      self.menu.popup(QCursor.pos())

    def insertRow(self, row):
      logging.info("SequenceTableView::insertRow() is running")
      self.model.insertRows(row + 1, 1)
      #self.adjustSize()

    def removeRowKeepStepOff(self, row):
      logging.info("SequenceTableView::removeRowKeepStepOff() is running")
      self.model.removeRowsKeepStepOff(row, 1)
      #self.adjustSize()

    def removeRowKeepStartOff(self, row):
      logging.info("SequenceTableView::removeRowKeepStartOff() is running")
      self.model.removeRowsKeepStartOff(row, 1)
      #self.adjustSize()

class SequenceDialog(QWidget):

    def __init__(self, args):

        super(SequenceDialog, self).__init__()

        self.args = args 

        # create pv objects
        self.pvSerMaxLen = PV(args.device + ':SerMaxLen-O')
        self.pvLength = PV(args.device + ':seq0Ctrl-Length-I')
        self.pvCycles = PV(args.device + ':seq0Ctrl-Cycles-I')
        self.pvSeq0Ser0 = PV(args.device + ':seq0Ser0-Data-I')
        self.pvSeq0Ser1 = PV(args.device + ':seq0Ser1-Data-I')
        self.pvSeq0Ser2 = PV(args.device + ':seq0Ser2-Data-I')
        self.pvSeq0Ser3 = PV(args.device + ':seq0Ser3-Data-I')
        self.pvSeq0Ser4 = PV(args.device + ':seq0Ser4-Data-I')
        self.pvSeq0Ser5 = PV(args.device + ':seq0Ser5-Data-I')
        self.pvSeq0Ser6 = PV(args.device + ':seq0Ser6-Data-I')
        self.pvSeq0Ser7 = PV(args.device + ':seq0Ser7-Data-I')
        self.pvSeq0Ser8 = PV(args.device + ':seq0Ser8-Data-I')
        self.pvSeq0Ser9 = PV(args.device + ':seq0Ser9-Data-I')
        self.pvSeq0Ser10 = PV(args.device + ':seq0Ser10-Data-I')
        self.pvSeq0Ser11 = PV(args.device + ':seq0Ser11-Data-I')
        self.pvSeq0Ser12 = PV(args.device + ':seq0Ser12-Data-I')
        self.pvSeq0Ser13 = PV(args.device + ':seq0Ser13-Data-I')
        self.pvSeq0Ser14 = PV(args.device + ':seq0Ser14-Data-I')
        self.pvSeq0Ser15 = PV(args.device + ':seq0Ser15-Data-I')
        self.pvSeq0Ser16 = PV(args.device + ':seq0Ser16-Data-I')
        self.pvSeq0Ser17 = PV(args.device + ':seq0Ser17-Data-I')
        self.pvSeq0Ser18 = PV(args.device + ':seq0Ser18-Data-I')
        self.pvSeq0Ser19 = PV(args.device + ':seq0Ser19-Data-I')
        self.pvStart = PV(args.device + ':seq0Ctrl-Start-I')
        self.pvStop = PV(args.device + ':seq0Ctrl-Stop-I')
        self.pvStatus = PV(args.device + ':seq0Ctrl-IsRunning-O')
        self.pvStartedAt = PV(args.device + ':seq0Ctrl-StartedAt-O')

        # create widgets
        self.createWidgets()

        # connect slots
        self.__btnDown.clicked.connect(self.btnDownAction)
        self.__btnUp.clicked.connect(self.btnUpAction)
        self.__btnStart.clicked.connect(self.btnStartAction)
        self.__btnStop.clicked.connect(self.btnStopAction)
        self.__btnInsertRow.clicked.connect(self.btnInsertRowAction)
        self.__btnRemoveRow.clicked.connect(self.btnRemoveRowAction)
        self.connect(self, SIGNAL("seqCtrlStatusChange"), self.emitStatusChange)
        self.connect(self, SIGNAL("seqCtrlStartedAtChange"), self.emitStartedAtChange)
        self.connect(self, SIGNAL("uploadSequence"), self.uploadSequence)

        # add pv monitor callbacks
        self.pvStatus.add_callback(self.__on_pv_status_changes)
        self.pvStartedAt.add_callback(self.__on_pv_started_at_changes)

        # ensure status of gui is updated after start up
        self.emit(SIGNAL("seqCtrlStatusChange"))
        self.emit(SIGNAL("seqCtrlStartedAtChange"))
        self.emit(SIGNAL("uploadSequence"))

    def createWidgets(self):

        # set GUI title
        self.setWindowTitle("CTA GUI " + self.args.esx)

        # create model
        headers = ["Step Offset", "Start Offset", "Event Codes"]
        initialSequence = [[0, 0, 200]]
        self.__localEvents = range(200, 220)
        self.__serMaxLen = self.pvSerMaxLen.get()
        self.__model = SequenceTableModel(self, self.__serMaxLen,
            initialSequence, headers, self.__localEvents)

        # create top layouts
        horizontal_layout = QHBoxLayout()
        vertical0_layout = QVBoxLayout()
        vertical1_layout = QVBoxLayout()

        # sequence upload/download group
        self.__labelTable = QLabel('sequence in table')
        self.__labelCompare = QLabel()
        self.__labelCompare.setAlignment(Qt.AlignCenter);
        self.setCompare(SequenceState.UNKNOWN)
        self.__labelIoc = QLabel('sequence on IOC')
        self.__btnDown = QPushButton('-->', self)
        self.__btnUp = QPushButton('<--', self)
        self.__grpb_seq_load = QGroupBox('sequence upload/download')
        vbl = QVBoxLayout()
        hbl = QHBoxLayout()
        hbl.addWidget(self.__labelTable)
        hbl.addWidget(self.__labelCompare)
        hbl.addWidget(self.__labelIoc)
        vbl.addLayout(hbl)
        vbl.addWidget(self.__btnDown)
        vbl.addWidget(self.__btnUp)
        self.__grpb_seq_load.setLayout(vbl)
        vertical0_layout.addWidget(self.__grpb_seq_load)

        # sequence definition group
        self.__tableView = SequenceTableView(self, self.__model)
        #self.__tableView.resizeColumnsToContents()
        self.__grpb_table = QGroupBox('sequence definition')
        self.__btnInsertRow = QPushButton('insert row')
        self.__btnRemoveRow = QPushButton('remove row')
        vbl = QVBoxLayout()
        vbl.addWidget(self.__tableView)
        hbl = QHBoxLayout()
        hbl.addWidget(self.__btnInsertRow)
        hbl.addWidget(self.__btnRemoveRow)
        vbl.addLayout(hbl)
        self.__grpb_table.setLayout(vbl)
        vertical0_layout.addWidget(self.__grpb_table)

        # run status group
        self.__btnStart = QPushButton('start', self)
        self.__btnStop = QPushButton('stop', self)
        self.__labelStatus = QLabel('status', self)
        self.__leditStatus = QLineEdit(self)
        self.__labelStartedAt = QLabel('started at', self)
        self.__leditStartedAt = QLineEdit(self)
        self.__leditStartedAt.setDisabled(True)
        self.__grpb_run_status = QGroupBox('run status', self)
        self.__leditStatus.setDisabled(True)
        vbl = QVBoxLayout()
        hbl = QHBoxLayout()
        hbl.addWidget(self.__btnStart)
        hbl.addWidget(self.__btnStop)
        vbl.addLayout(hbl)
        hbl = QHBoxLayout()
        hbl.addWidget(self.__labelStatus)
        hbl.addWidget(self.__leditStatus)
        vbl.addLayout(hbl)
        hbl = QHBoxLayout()
        hbl.addWidget(self.__labelStartedAt)
        hbl.addWidget(self.__leditStartedAt)
        vbl.addLayout(hbl)
        self.__grpb_run_status.setLayout(vbl)
        vertical1_layout.addWidget(self.__grpb_run_status)

        # repetition configuration group
        self.__rbtn_repetitions = QRadioButton('number of repetitions')
        self.__sb_repetitions = QSpinBox()
        self.__rbtn_forever = QRadioButton('forever')
        self.__rbtn_repetitions.setChecked(True)
        self.__grpb_repetitions = QGroupBox('repetition configuration', self)
        self.__sb_repetitions.setRange(1, 65536) # 16 bit
        hbl = QHBoxLayout()
        vbl = QVBoxLayout()
        hbl.addWidget(self.__rbtn_repetitions)
        hbl.addWidget(self.__sb_repetitions)
        vbl.addLayout(hbl)
        vbl.addWidget(self.__rbtn_forever)
        self.__grpb_repetitions.setLayout(vbl)
        vertical1_layout.addWidget(self.__grpb_repetitions)

        # start configuration group
        self.__rbtn_immediatly = QRadioButton('start immediately')
        self.__rbtn_immediatly.setChecked(True)
        self.__grpb_start_config = QGroupBox("start configuration", self)
        vbl = QVBoxLayout()
        vbl.addWidget(self.__rbtn_immediatly)
        self.__grpb_start_config.setLayout(vbl)
        vertical1_layout.addWidget(self.__grpb_start_config)

        horizontal_layout.addLayout(vertical0_layout)
        horizontal_layout.addLayout(vertical1_layout)

        self.setLayout(horizontal_layout)

    def btnDownAction(self):

        logging.info('button down has been pressed')

        series = self.__model.getSeries()

        self.pvLength.put(len(series[0]))

        self.pvSeq0Ser0.put(numpy.array(series[0]), wait=True)
        self.pvSeq0Ser1.put(numpy.array(series[1]), wait=True)
        self.pvSeq0Ser2.put(numpy.array(series[2]), wait=True)
        self.pvSeq0Ser3.put(numpy.array(series[3]), wait=True)
        self.pvSeq0Ser4.put(numpy.array(series[4]), wait=True)
        self.pvSeq0Ser5.put(numpy.array(series[5]), wait=True)
        self.pvSeq0Ser6.put(numpy.array(series[6]), wait=True)
        self.pvSeq0Ser7.put(numpy.array(series[7]), wait=True)
        self.pvSeq0Ser8.put(numpy.array(series[8]), wait=True)
        self.pvSeq0Ser9.put(numpy.array(series[9]), wait=True)
        self.pvSeq0Ser10.put(numpy.array(series[10]), wait=True)
        self.pvSeq0Ser11.put(numpy.array(series[11]), wait=True)
        self.pvSeq0Ser12.put(numpy.array(series[12]), wait=True)
        self.pvSeq0Ser13.put(numpy.array(series[13]), wait=True)
        self.pvSeq0Ser14.put(numpy.array(series[14]), wait=True)
        self.pvSeq0Ser15.put(numpy.array(series[15]), wait=True)
        self.pvSeq0Ser16.put(numpy.array(series[16]), wait=True)
        self.pvSeq0Ser17.put(numpy.array(series[17]), wait=True)
        self.pvSeq0Ser18.put(numpy.array(series[18]), wait=True)
        self.pvSeq0Ser19.put(numpy.array(series[19]), wait=True)

        self.setCompare(SequenceState.EQUAL)

    def btnUpAction(self):
        logging.info('button up has been pressed')
        self.uploadSequence()

    def btnStartAction(self):
        logging.info('button start has been pressed')
        if self.__rbtn_forever.isChecked():
            repetitions = 0
        else:
            repetitions = self.__sb_repetitions.value()
        self.pvCycles.put(repetitions)
        self.pvStart.put(1)

    def btnStopAction(self):
        logging.info('button stop has been pressed')
        self.pvStop.put(1)

    def btnInsertRowAction(self):
        logging.info('button "insert row" has been pressed')
        self.__model.insertRows(self.__model.rowCount(self), 1)

    def btnRemoveRowAction(self):
        logging.info('button "remove row" has been pressed')
        self.__model.removeRowsKeepStepOff(self.__model.rowCount(self) - 1, 1)

    def emitStatusChange(self):

        logging.info('SequenceDialog.emitStatusChange is running')

        # get status and set/enable/disable related widgets
        value = self.pvStatus.get()
        if value == 0:
            self.__leditStatus.setText('stopped')
            self.__grpb_repetitions.setDisabled(False)
            self.__grpb_start_config.setDisabled(False)
            self.__btnStart.setDisabled(False)
            self.__btnStop.setDisabled(True)
        else:
            self.__leditStatus.setText('running')
            self.__grpb_repetitions.setDisabled(True)
            self.__grpb_start_config.setDisabled(True)
            self.__btnStart.setDisabled(True)
            self.__btnStop.setDisabled(False)

        # get repetitions and set related widgets
        repetitions = self.pvCycles.get()
        if repetitions == 0:
            self.__rbtn_forever.setChecked(True)
            self.__rbtn_repetitions.setChecked(False)
        else:
            self.__rbtn_forever.setChecked(False)
            self.__rbtn_repetitions.setChecked(True)
            self.__sb_repetitions.setValue(repetitions)

        logging.info('SequenceDialog.leaving emitStatusChange')

    def emitStartedAtChange(self):

        logging.info('SequenceDialog.emitStartedAtChange is running')

        # get new startedAt value and set widget
        self.__leditStartedAt.setText(str(int(self.pvStartedAt.get())))

        logging.info('SequenceDialog.leaving emitStartedAtChange')

    def uploadSequence(self):

        logging.info('SequenceDialog.uploadSequence() is running')

        series = [None] * len(self.__localEvents)

        length = self.pvSeq0Ser0.count

        if  length > 1:
            series[0] = self.pvSeq0Ser0.get().tolist()
            series[1] = self.pvSeq0Ser1.get().tolist()
            series[2] = self.pvSeq0Ser2.get().tolist()
            series[3] = self.pvSeq0Ser3.get().tolist()
            series[4] = self.pvSeq0Ser4.get().tolist()
            series[5] = self.pvSeq0Ser5.get().tolist()
            series[6] = self.pvSeq0Ser6.get().tolist()
            series[7] = self.pvSeq0Ser7.get().tolist()
            series[8] = self.pvSeq0Ser8.get().tolist()
            series[9] = self.pvSeq0Ser9.get().tolist()
            series[10] = self.pvSeq0Ser10.get().tolist()
            series[11] = self.pvSeq0Ser11.get().tolist()
            series[12] = self.pvSeq0Ser12.get().tolist()
            series[13] = self.pvSeq0Ser13.get().tolist()
            series[14] = self.pvSeq0Ser14.get().tolist()
            series[15] = self.pvSeq0Ser15.get().tolist()
            series[16] = self.pvSeq0Ser16.get().tolist()
            series[17] = self.pvSeq0Ser17.get().tolist()
            series[18] = self.pvSeq0Ser18.get().tolist()
            series[19] = self.pvSeq0Ser19.get().tolist()
        elif length == 1:
            series[0] = [self.pvSeq0Ser0.get()]
            series[1] = [self.pvSeq0Ser1.get()]
            series[2] = [self.pvSeq0Ser2.get()]
            series[3] = [self.pvSeq0Ser3.get()]
            series[4] = [self.pvSeq0Ser4.get()]
            series[5] = [self.pvSeq0Ser5.get()]
            series[6] = [self.pvSeq0Ser6.get()]
            series[7] = [self.pvSeq0Ser7.get()]
            series[8] = [self.pvSeq0Ser8.get()]
            series[9] = [self.pvSeq0Ser9.get()]
            series[10] = [self.pvSeq0Ser10.get()]
            series[11] = [self.pvSeq0Ser11.get()]
            series[12] = [self.pvSeq0Ser12.get()]
            series[13] = [self.pvSeq0Ser13.get()]
            series[14] = [self.pvSeq0Ser14.get()]
            series[15] = [self.pvSeq0Ser15.get()]
            series[16] = [self.pvSeq0Ser16.get()]
            series[17] = [self.pvSeq0Ser17.get()]
            series[18] = [self.pvSeq0Ser18.get()]
            series[19] = [self.pvSeq0Ser19.get()]
        else:
            for i in range(len(self.__localEvents)):
                series[i] = [0]

        self.__model.setSeries(series)

        self.__model.reset()

        self.setCompare(SequenceState.EQUAL)

        logging.info('SequenceDialog.uploadSequence() is done')

    def __on_pv_status_changes(self, pvname=None, value=None, char_value=None,
        **kw):
        logging.info('pv status has changed, value=' + str(value))
        self.emit(SIGNAL("seqCtrlStatusChange"), value)

    def __on_pv_started_at_changes(self, pvname=None, value=None, char_value=None,
        **kw):
        logging.info('pv startedAt has changed, value=' + str(value))
        self.emit(SIGNAL("seqCtrlStartedAtChange"), value)

    def setCompare(self, state):

        if state is SequenceState.EQUAL:
            self.__labelCompare.setText('  ==  ')
            self.__labelCompare.setStyleSheet("QLabel { background-color : green; color : black; }");
        elif state is SequenceState.UNEQUAL:
            self.__labelCompare.setText('  !=  ')
            self.__labelCompare.setStyleSheet("QLabel { background-color : red; color : black; }");
        elif state is SequenceState.UNKNOWN:
            self.__labelCompare.setText('  ??  ')
            self.__labelCompare.setStyleSheet("QLabel { background-color : orange; color : black; }");

if __name__ == '__main__':
    
    # setup parser
    parser = argparse.ArgumentParser()
    parser.add_argument('esx', help='Specify experimental station for which '
        'the CTA GUI shall be started.', choices=['ESA', 'ESB'])
    parser.add_argument('device', help='Name of device running CTA.')
    parser.add_argument('-l', '--loglevel', help='Specify level for logging '
        '(used for debugging)'
        , choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        default = 'WARNING')
    args = parser.parse_args()

    # setup logging
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=numeric_level, format='%(asctime)s | %(levelname)8s | %(message)s')
    
    # setup application
    app = QApplication(sys.argv)
    app.setStyle("plastique")

    # setup dialog
    dialog = SequenceDialog(args)
    dialog.show()
    
    # run application
    sys.exit(app.exec_())

