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
    if 'status' in data:
        p_v = 'status'
        value = data['status']
    elif 'started at' in data:
        p_v = 'started at'
        value = data['started at']
    else:
        raise RuntimeError('Invalid data received')
    print(">> status callback 1 has been called (pv=" + p_v + ", value=" + str(value) + ")")

    # use lib
    if p_v == 'started at':
        # get started at
        print('>> reading back at what pulse id the sequence was started')
        started_at = lib.get_started_at()
        print('>> the sequence started at pulse id ' + str(started_at))

def run_status_callback_2(data):
    """
    function to demonstrate callaback functionality
    """
    # use data
    if 'status' in data:
        p_v = 'status'
        value = data['status']
    elif 'started at' in data:
        p_v = 'started at'
        value = data['started at']
    else:
        raise RuntimeError('Invalid data received')
    print(">> status callback 2 has been called (pv=" + p_v + ", value=" + str(value) + ")")

def repetition_config_callback_1(config, lib):
    """
    function to demonstrate callaback functionality
    """

    # use config
    if config['mode'] == CtaLib.RepetitionMode.FOREVER:
        print(">> repetition config callback 1 has been called (forever)")
    elif config['mode'] == CtaLib.RepetitionMode.NTIMES:
        print(">> repetition config callback 1 has been called (" + str(config['n'])
              + " times)")
    else:
        RuntimeError('Invalid mode received')
    
    # use lib
    if lib.is_running():
        is_running = " "
    else:
        is_running = " not "
    print(">> Reading back is_running. Sequence is" + is_running + "running")

    
def repetition_config_callback_2(config):
    """
    function to demonstrate callaback functionality
    """

    # use config
    if config['mode'] == CtaLib.RepetitionMode.FOREVER:
        print(">> repetition config callback 2 has been called (forever)")
    elif config['mode'] == CtaLib.RepetitionMode.NTIMES:
        print(">> repetition config callback 2 has been called (" + str(config['n'])
              + " times)")
    else:
        RuntimeError('Invalid mode received')
    
def sequence_callback_1(sequence, lib):
    """
    function to demonstrate callaback functionality
    """

    if lib.is_running():
        is_running = ' '
    else:
        is_running = ' not '

    print(">> sequence callback 1 has been called (sequence=" + str(sequence)
          + "). The sequence is" + is_running + "running.")

def sequence_callback_2(sequence):
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
    lib.register_run_status_callback(run_status_callback_2)
    lib.register_repetition_config_callback(repetition_config_callback_1, lib)
    lib.register_repetition_config_callback(repetition_config_callback_2)
    lib.register_sequence_callback(sequence_callback_1, lib)
    lib.register_sequence_callback(sequence_callback_2)

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
    lib.set_repetition_config(config={'mode': CtaLib.RepetitionMode.FOREVER})
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
