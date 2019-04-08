"""
This is an example sript which demonstrates the usage of the cta_lib
python module.
"""
import time
import argparse
import cta_lib

def main():

    # setup parser
    parser = argparse.ArgumentParser() # pylint: disable=invalid-name
    parser.add_argument('device', help='Name of device running CTA.')
    parser.add_argument(
        '-l', '--loglevel', help='Specify level for logging '
        '(used for debugging)'
        , choices=['critical', 'error', 'warning', 'info', 'debug'],
        default='warning')
    args = parser.parse_args() # pylint: disable=invalid-name

    # create cta lib object
    lib = cta_lib.CtaLib(args.device, log_level=args.loglevel) # pylint: disable=no-member,invalid-name

    # exit if the cta is already running
    if lib.is_running():
        raise RuntimeError('cta is already running')

    # create sequence
    sequence = {} # pylint: disable=invalid-name

    series = [0] * 200 # pylint: disable=invalid-name
    for i in range(100):
        series[i] = 1
    sequence[200] = series

    series = [0] * 200 # pylint: disable=invalid-name
    for i in range(100, 200):
        series[i] = 1
    sequence[201] = series

    # upload
    print(">> uploading")
    lib.upload(sequence)

    # start
    print(">> starting forever")
    lib.start(0)

    # wait some time
    print(">> waiting some time before stopping")
    time.sleep(10)

    # stop
    print(">> stopping")
    lib.stop()

    # disconect pvs
    lib.disconnect_pvs()

if __name__ == '__main__':
    main()
