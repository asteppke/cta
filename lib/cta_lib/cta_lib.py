"""
The complex triggering application (CTA) is an application which allows the
user to inject a user defined sequence of events in a subtree of the timing
tree.
The CTA runs on an IOC. There are two ways to program and control it.
The first is via the GUI and the second is this python library.
"""
import logging
import time
import threading
import numpy
from epics import PV

class CtaLib:
    """
    Create an object of this class to control one sequence of a CTA.
    """

    def __init__(self, device, sequence=0, log_level="warning"):
        """
        Constructor

        Arguments
        device: device name (e.g. SAR-CCTA-ESA)
        sequence: sequence number (default = 0)
        log_level: critical, error, warning, info, debug
        """
        self._constants = dict()
        self._constants['event_code_range_base'] = 200
        self._constants['num_of_event_codes'] = 20
        self._constants['num_of_pvs'] = 26

        # setup logging
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log_level: %s' % log_level)
        logging.basicConfig(level=numeric_level,
                            format='%(asctime)s | %(levelname)8s | %(message)s')
        logging.info('__init__() is running (device=' + device +')')

        # create threading event
        self._event = threading.Event()

        # create connection housekeeper
        self._num_connected = 0

        # create attributes for callback support
        self._status_callbacks = list()
        self._series_callbacks = list()

        # create pv objects
        self._pvs = dict()

        pv_name = device + ':SerMaxLen-O'
        self._pvs['SerMaxLen-O'] = PV(
            pv_name,
            connection_callback=self._connection_callback)

        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Length-I'
        self._pvs['Ctrl-Length-I'] = PV(
            pv_name,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Cycles-I'
        self._pvs['Ctrl-Cycles-I'] = PV(
            pv_name,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Start-I'
        self._pvs['Ctrl-Start-I'] = PV(
            pv_name,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-Stop-I'
        self._pvs['Ctrl-Stop-I'] = PV(
            pv_name,
            connection_callback=self._connection_callback)
        pv_name = device + ':seq' + str(sequence) + 'Ctrl-IsRunning-O'
        self._pvs['Ctrl-IsRunning-O'] = PV(
            pv_name,
            callback=self._status_callback,
            connection_callback=self._connection_callback)

        self._pvs['Data-I'] = list()
        for i in range(0, self._constants['num_of_event_codes']):
            pv_name = device + ':seq' + str(sequence) + 'Ser' + str(i) + '-Data-I'
            self._pvs['Data-I'].append(PV(
                pv_name,
                callback=self._series_callback,
                connection_callback=self._connection_callback))

        # wait for the connections to be established
        if not self._event.wait(timeout=5.0):
            raise RuntimeError('Some PV(s) is/are not connected')
        time.sleep(1) # NOTE01

        # logging
        for i in range(0, self._constants['num_of_event_codes']):
            logging.debug('NORD of ' + str(i) + ':' + str(self._pvs['Data-I'][i]))
        logging.info('__init__() is done')

    def __del__(self):
        """
        Deconstructor
        """

        logging.info('__del__() is running')

        logging.info('__del__() is done')

    def disconnect_pvs(self):
        """
        Disconnect all pvs

        Actually this should be done in the destructor.
        If we do we get the following error message:
          FATAL: exception not rethrown
          CA client library tcp receive thread terminating due to a
          non-standard C++ exception
        Reason unknown.
        """
        logging.info('disconnect_pvs is running')

        # disconnect connections and clear all callbacks
        for key, pv in self._pvs.items(): # pylint: disable=C0103
            if key == 'Data-I':
                for i in range(0, self._constants['num_of_event_codes']):
                    pv[i].disconnect()
            else:
                pv.disconnect()

        logging.info('disconnect_pvs is done')

    def get_max_length(self):
        """
        Get the maximal length of a sequence

        Return
        max_length: maximal length of a sequence
        """
        logging.info('get_max_length() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get max length
        max_length = self._pvs['SerMaxLen-O'].get()

        logging.info('get_max_length() is done')

        return max_length

    def get_length(self):
        """
        Get the length of the sequence on the IOC

        Return
        length: length of the sequence
        """
        logging.info('get_length() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get length
        length = self._pvs['Ctrl-Length-I'].get()

        logging.info('get_length() is done')

        return length

    def upload(self, seq):
        """
        Upload a sequence to the IOC

        Arguments
        seq: The sequence to be uploaded to the IOC.
             A sequence is a dictionary where each key value pair represents a series.
             A series is a list of 0's and 1's which defines, if the corresponding event code
             is sent in the corresponding machine pulse.
             The key is an integer and represents the event code.
             The value is the series.
             If a certain event code is not sent in the sequence, it may or may not
             not be present in the dictionary.
             Example:
                 seq = {200: [1, 0], 201: [1, 1]}
                 =>
                 machine pulse     x: event code 200 is sent
                 machine pulse x + 1: event code 200 and 201 are sent
        """

        logging.info('upload() is running')

        # check the sequence
        self.check_sequence(seq)

        # fill empty series
        seq = self.fill_empty_series(seq)

        # logging
        logging.debug('upload() upload: ' + str(seq))

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # upload seq to pvs
        for i in range(0, self._constants['num_of_event_codes']):
            self._pvs['Data-I'][i].put(
                numpy.array(seq[self._constants['event_code_range_base'] + i]), wait=True)

        # set length
        self._pvs['Ctrl-Length-I'].put(len(seq[self._constants['event_code_range_base']]),
                                       wait=True)

        logging.info('upload() is done')

    def download(self):
        """
        Download a sequence from the IOC

        Return
        seq: The sequence downloaded from the IOC.
             Refer to the upload method for a definition of seq.
        """

        logging.info('download() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # download
        seq = {}
        for i in range(0, self._constants['num_of_event_codes']):
            logging.debug('NORD of ' + str(i) + ':' + str(self._pvs['Data-I'][i]))
            seq[self._constants['event_code_range_base'] + i] = numpy.atleast_1d(
                self._pvs['Data-I'][i].get()).tolist()

        # logging
        logging.debug('download() downloaded: ' + str(seq))

        # check the sequence
        self.check_sequence(seq)

        logging.info('download() is done')

        return seq

    def set_num_of_repetitions(self, repetitions):
        """
        Set the number of repetitions to the CTA.
        This is the number of times the sequence will be repeated when started.

        Arguments:
        repetitions: 0 = forever, x = x repetitions
        """
        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # set number of repetitions
        self._pvs['Ctrl-Cycles-I'].put(repetitions, wait=True)

    def get_num_of_repetitions(self):
        """
        Get the number of repetitions from the CTA.
        This is the number of times the sequence will be repeated when started.

        Return
        repetitions: 0 = forever, x = x repetitions
        """
        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get number of repetitions
        repetitions = self._pvs['Ctrl-Cycles-I'].get()

        return repetitions

    def start(self, repetitions=None):
        """
        Start CTA

        Arguments
        repetitions: 0 = forever, x = x repetitions
                     defaut: do not set number of repetitions, last value on IOC will be used
        """

        logging.info('start() is running (repetitions=' + str(repetitions) + ')')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # set number of repetitions
        if repetitions is not None:
            self._pvs['Ctrl-Cycles-I'].put(repetitions, wait=True)

        # start
        self._pvs['Ctrl-Start-I'].put(1, wait=True)

        logging.info('start() is done')

    def stop(self):
        """
        Stop CTA

        """

        logging.info('stop() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        self._pvs['Ctrl-Stop-I'].put(1, wait=True)

        logging.info('stop() is done')

    def is_running(self):
        """
        Check if CTA is running

        Return
        True if CTA is running, False otherwise
        """

        logging.info('is_running() is running')

        # check connections
        is_all_connected = self._event.wait(timeout=5.0)
        if not is_all_connected:
            raise RuntimeError('Some PV(s) is/are not connected')

        # get status
        is_running = bool(self._pvs['Ctrl-IsRunning-O'].get() != 0)

        logging.info('is_running() is done')

        return is_running

    def register_status_callback(self, callback):
        """
        This function can be used to register a callback function which is
        called if the status of the sequence controller changed.

        The following arguments will be passed to the callback function:
            value: 1 if sequence is running, 0 otherwise

        Keep your callback function short.

        Arguments
        callback: Function to be called.
        """
        self._status_callbacks.append(callback)

    def register_series_callback(self, callback):
        """
        This function can be used to register a callback function which is
        called if a series of the sequence on the IOC has changed.

        Refer to the upload method for a definition of a sequence.

        The following arguments will be passed to the callback function:
            sequence: sequence containing the series which has changed

        Keep your callback function short.

        Arguments
        callback: Function to be called
        """
        self._series_callbacks.append(callback)

    def check_sequence(self, seq):
        """
        Check if a sequence is valid

        Arguments
        seq: The sequence to be checked.
                  A RunTimeError exception is thrown if the sequence is not valid.
                  Refer to the upload method for a definition of seq.
        """

        logging.info('check_sequence() is running')

        # check that seq has correct types and at least one series
        if not isinstance(seq, dict):
            raise RuntimeError("seq arg is not a dictionary")
        if not seq:
            raise RuntimeError("dictionary seq is empty")
        for key, series in seq.items():
            if not isinstance(key, int):
                raise RuntimeError("dictionary contains key value pair where key is"
                                   " not an int")
            if not isinstance(series, list):
                raise RuntimeError("dictionary contains key value pair where value is"
                                   " not a list")
            for item in series:
                if item != 0 and item != 1:
                    raise RuntimeError(
                        "dictionary contains key value pair where value is"
                        " is a list with at least one element which is not 0 or 1")

        # check that all series have same length
        length = len(seq[list(seq)[0]])
        for key, series in seq.items():
            if len(seq[key]) != length:
                raise RuntimeError(
                    "dictionary contains key value pair where at least"
                    " two values are lists with different length")

        # check that series are not too long
        length = len(seq[list(seq)[0]])
        if length > self._pvs['SerMaxLen-O'].get():
            raise RuntimeError(
                "dictionary contains key value pair where the values "
                "are lists with too many elements")

        logging.info('check_sequence() is done')

    def fill_empty_series(self, seq):
        """
        Fill the sequence such that all events are described

        Arguments
        seq: A sequence where some events might not be defined.

        Return
        seq: The sequence with all events defined.

        Refer to the upload method for a definition of seq.
        """


        logging.info('fill_empty_series() is running')

        length = len(seq[self._constants['event_code_range_base']])
        for event_code in range(self._constants['event_code_range_base'],
                                self._constants['event_code_range_base'] +
                                self._constants['num_of_event_codes']):
            if event_code not in seq:
                seq[event_code] = [0] * length

        logging.info('fill_empty_series() is done')

        return seq

    def print(self, seq):
        """
        Print the sequence to std output

        Arguments
        seq: The sequence to be printed.
                  Refer to the upload method for a definition of seq.
        """

        logging.info('print() is running')
        logging.debug('print() prints: ' + str(seq))

        # check the sequence
        self.check_sequence(seq)

        length = len(seq[list(seq)[0]])

        print('      | <---------------- event -------------->')
        print('      | 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2')
        print('      | 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1 1')
        print('pulse | 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9')
        print('-----------------------------------------------')
        for i in range(length):
            print(repr(i).rjust(5), '|', end='')
            for event_code in range(self._constants['event_code_range_base'],
                                    self._constants['event_code_range_base'] +
                                    self._constants['num_of_event_codes']):
                print("{state}".format(state=seq[event_code][i]).rjust(2), end='')
            print()

        logging.info('print() is done')

    def _status_callback(self, **kwargs):
        """
        Callback function which is called when the status PV changes the value.
        It is used to call user callback functions which registered for
        for this event.
        """
        logging.info('_status_callback() is running (value=' + str(kwargs['value']) + ')')

        logging.info('calling status callbacks next')
        for callback in self._status_callbacks:
            callback(kwargs['value'])
        logging.info('calling status callbacks done')

    def _series_callback(self, **kwargs):
        """
        Callback function which is called when one of the PVs holding a series of
        the sequence changes the value. It is used to call user callback functions which
        registered for this event.
        """
        logging.info('_series_callback() is running (pv=' + kwargs['pvname'] +
                     ', value=' + str(kwargs['value']))

        # determine event number from pvname
        for idx, pv in enumerate(self._pvs['Data-I']): # pylint: disable=C0103
            if pv.pvname == kwargs['pvname']:
                event_number = self._constants['event_code_range_base'] + idx
                break

        # create sequence
        seq = {}
        seq[event_number] = numpy.atleast_1d(kwargs['value']).tolist()

        # call callbacks
        logging.info('calling sequence callbacks next')
        for callback in self._series_callbacks:
            callback(seq)
        logging.info('calling sequence callbacks done')

        logging.info('_series_callback() is done')

    def _connection_callback(self, **kwargs):
        """
        Callback function used internally to do connection status housekeeping

        Arguments
        pvname: name of PV for which the callback is called
        conn: status of the connection
        """

        logging.info('_connection_callback() is running (pvname=' + kwargs['pvname'] +
                     ', conn=' + repr(kwargs['conn']) + ', thread_id=' +
                     str(threading.get_ident()) +')')

        # do connection housekeeping
        if kwargs['conn']:
            self._num_connected += 1
        else:
            self._num_connected -= 1
        logging.debug('_num_connected=' + str(self._num_connected))

        # signal to other thread
        if self._num_connected == self._constants['num_of_pvs']:
            self._event.set()
        else:
            self._event.clear()

        logging.info('_connection_callback() is done')

# NOTE01
# This sleep is needed for the initial ca communication to be completed.
# If it is not there and the upload is called right after object creation,
# the number of elements in the PV has not arrived in python for all PVs.
# This leads to a fail of check_sequence().
