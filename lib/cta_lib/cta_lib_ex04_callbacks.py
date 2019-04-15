"""
This is an example sript which demonstrates the usage of the cta_lib
python module.
"""
import argparse
import time
from cta_lib import CtaLib

def run_status_callback_1(data, lib):
    """
    function to demonstrate callaback functionality
    """
    # use data
    p_v, value = list(data.items())[0]
    print(">> status callback 1 has been called (pv=" + p_v + ", value=" + str(value) + ")")

    if p_v == 'started at':
        # get started at
        print('>> reading back at what pulse id the sequence was started')
        started_at = lib.get_started_at()
        print('>> the sequence started at pulse id ' + str(started_at))

def run_status_callback_2(data, lib):
    """
    function to demonstrate callaback functionality
    """
    # use data
    p_v, value = list(data.items())[0]
    print(">> status callback 2 has been called (pv=" + p_v + ", value=" + str(value) + ")")

    if p_v == 'started at':
        # get started at
        print('>> reading back at what pulse id the sequence was started')
        started_at = lib.get_started_at()
        print('>> the sequence started at pulse id ' + str(started_at))

def sequence_callback_1(sequence, user_object):
    """
    function to demonstrate callaback functionality
    """
    print(">> sequence callback 1 has been called (sequence=" + str(sequence) + ")")

def sequence_callback_2(sequence, user_object):
    """
    function to demonstrate callaback functionality
    """
    print(">> sequence callback 2 has been called (sequence=" + str(sequence) + ")")

def main():
    """
    The main function contains the example script.
    """

    # setup parser
    parser = argparse.ArgumentParser()
    parser.add_argument('device', help='Name of device running CTA.')
    parser.add_argument(
        '-l', '--loglevel', help='Specify level for logging '
        '(used for debugging)'
        , choices=['critical', 'error', 'warning', 'info', 'debug'],
        default='warning')
    args = parser.parse_args()

    # create cta lib object
    lib = CtaLib(args.device, log_level=args.loglevel)

    # exit if the cta is already running
    if lib.is_running():
        raise RuntimeError('cta is already running')

    # register callbacks
    lib.register_run_status_callback(run_status_callback_1, lib)
    lib.register_run_status_callback(run_status_callback_2, lib)
    lib.register_sequence_callback(sequence_callback_1, lib)
    lib.register_sequence_callback(sequence_callback_2, lib)

    # create sequence
    sequence = {}
    sequence[200] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[201] = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[202] = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[203] = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[204] = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[205] = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[206] = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[207] = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[208] = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[209] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[210] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[211] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    sequence[212] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    sequence[213] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
    sequence[214] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
    sequence[215] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    sequence[216] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
    sequence[217] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
    sequence[218] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
    sequence[219] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    # upload
    print('>> uploading')
    lib.upload(sequence)

    # set repetition configuration
    print(">> setting repetition configuration (10 times)")
    lib.set_repetition_config(config={'mode': CtaLib.RepetitionMode.NTIMES, 'n': 10})

    # start
    print(">> starting")
    lib.start()
    time.sleep(0.2) # wait for the cta to process the start command

    # poll for completion
    while lib.is_running():
        print(">> still running")
        time.sleep(1)
    print(">> run has completed")

    # disconect pvs
    lib.disconnect_pvs()

if __name__ == '__main__':
    main()
