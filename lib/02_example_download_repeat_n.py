import cta_lib
import time
import argparse
import sys

if __name__ == '__main__':
  
  # setup parser
  parser = argparse.ArgumentParser()
  parser.add_argument('device', help='Name of device running CTA.')
  parser.add_argument('-l', '--loglevel', help='Specify level for logging '
      '(used for debugging)'
      , choices=['critical', 'error', 'warning', 'info', 'debug'],
      default = 'warning')
  args = parser.parse_args()

  # create cta lib object
  lib = cta_lib.CtaLib(args.device, log_level=args.loglevel)

  # exit if the cta is already running
  if lib.is_running():
    raise RuntimeError('cta is already running')
    sys.exit()

  # create sequence
  sequence = {}

  series = [0] * 200
  for i in range(100):
    series[i] = 1
  sequence[200] = series

  series = [0] * 200
  for i in range(100,200):
    series[i] = 1
  sequence[201] = series

  # upload
  print(">> uploading")
  lib.upload(sequence)

  # start
  print(">> starting (10 repetitions)")
  lib.start(10)
  time.sleep(0.2) # wait for the cta to process the start command

  # poll for completion
  while lib.is_running():
    print(">> still running")
    time.sleep(1)
  print(">> run has completed")

  # disconect pvs
  lib.disconnect_pvs()

