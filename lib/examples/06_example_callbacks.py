import cta_lib
import argparse
import time

def status_callback_1(value):
  print(">> status callback 1 has been called (value=" + str(value) + ")")

def status_callback_2(value):
  print(">> status callback 2 has been called (value=" + str(value) + ")")

def series_callback_1(seq):
  print(">> sequence callback 1 has been called (seq=" + str(seq) + ")")

def series_callback_2(seq):
  print(">> sequence callback 2 has been called (seq=" + str(seq) + ")")

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

  # register callbacks
  lib.register_status_callback(status_callback_1)
  lib.register_status_callback(status_callback_2)
  lib.register_series_callback(series_callback_1)
  lib.register_series_callback(series_callback_2)

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

  # download
  print('>> downloading')
  lib.download(sequence)

  # start
  print(">> starting (20 repetition)")
  lib.start(20)

  # poll for completion
  while lib.is_running():
    print(">> still running")
    time.sleep(1)
  print(">> run has completed")

