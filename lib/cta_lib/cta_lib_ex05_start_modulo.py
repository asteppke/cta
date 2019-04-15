"""
This is an example sript which demonstrates the usage of the cta_lib
python module.
"""
import argparse
import threading
from cta_lib import CtaLib

def run_status_callback(data, user_object):
    """
    This function is called by cta_lib if an item of the run status has
    changed. The function detects when the sequence has completed on the IOC
    and wakes up the main thread.
    """

    print('## run_status_callback() is running data=' + str(data))

    if 'status' in data:
        status = data['status']
        if status == 0:
            start_config = user_object['lib'].get_start_config()
            print('## run with start config ' + str(start_config) + ' has completed')
            user_object['event'].set()
        elif status == 1:
            pass
        else:
            raise RuntimeError('Unexpected status received')

def main(): # pylint: disable=R0915
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

    # create threading event
    event = threading.Event()

    # create user_object
    user_object = {'lib': lib, 'event': event}

    # register for run status callback
    lib.register_run_status_callback(run_status_callback, user_object)

    # create sequence
    sequence = {}

    series = [0] * 200
    for i in range(100):
        series[i] = 1
    sequence[200] = series

    series = [0] * 200
    for i in range(100, 200):
        series[i] = 1
    sequence[201] = series

    # upload
    print(">> uploading")
    lib.upload(sequence)

    # set start config, start and wait
    start_config = {'mode': CtaLib.StartMode.IMMEDIATE}
    print('!! setting start configuration (' + str(start_config) + ')')
    lib.set_start_config(config=start_config)
    print(">> starting once")
    event.clear()
    lib.start(1)
    print('>> waiting until sequence is played out')
    if not event.wait(timeout=5.0):
        raise RuntimeError('Sequence did not complete in time')
    print('>> sequence completed, moving on')

    # set start config, start and wait
    start_config = {'mode': CtaLib.StartMode.MODULO}
    print('!! setting start configuration (' + str(start_config) + ')')
    print('>> setting start configuration')
    lib.set_start_config(config=start_config)
    print(">> starting once")
    event.clear()
    lib.start(1)
    print('>> waiting until sequence is played out')
    if not event.wait(timeout=5.0):
        raise RuntimeError('Sequence did not complete in time')
    print('>> sequence completed, moving on')

    # set start config, start and wait
    start_config = {'mode': CtaLib.StartMode.MODULO, 'divisor': 10, 'offset': 3}
    print('!! setting start configuration (' + str(start_config) + ')')
    print('>> setting start configuration')
    lib.set_start_config(config=start_config)
    print(">> starting once")
    event.clear()
    lib.start(1)
    print('>> waiting until sequence is played out')
    if not event.wait(timeout=5.0):
        raise RuntimeError('Sequence did not complete in time')
    print('>> sequence completed, moving on')

    # set start config, start and wait
    start_config = {'mode': CtaLib.StartMode.MODULO, 'divisor': 5}
    print('!! setting start configuration (' + str(start_config) + ')')
    print('>> setting start configuration')
    lib.set_start_config(config=start_config)
    print(">> starting once")
    event.clear()
    lib.start(1)
    print('>> waiting until sequence is played out')
    if not event.wait(timeout=5.0):
        raise RuntimeError('Sequence did not complete in time')
    print('>> sequence completed, moving on')

    # set start config, start and wait
    start_config = {'mode': CtaLib.StartMode.MODULO, 'offset': 1}
    print('!! setting start configuration (' + str(start_config) + ')')
    print('>> setting start configuration')
    lib.set_start_config(config=start_config)
    print(">> starting once")
    event.clear()
    lib.start(1)
    print('>> waiting until sequence is played out')
    if not event.wait(timeout=5.0):
        raise RuntimeError('Sequence did not complete in time')
    print('>> sequence completed, moving on')

    # disconect pvs
    print('>> disconnecting pvs')
    lib.disconnect_pvs()

if __name__ == '__main__':
    main()
