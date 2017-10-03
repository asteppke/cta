import unittest
from epics import PV
import numpy
import time
from subprocess import Popen, DEVNULL

class TestSeqCtrl(unittest.TestCase):

  def test_enalbeDisable(self):

    self.data = [1, 0, 1, 0, 1, 0, 1, 0]

    print('test_enalbeDisable')

    # create PV objects
    pvDataI = PV('MTEST-PC-BY84-CTA:ser0-Data-I')
    pvLoadI = PV('MTEST-PC-BY84-CTA:ser0-Load-I.PROC')
    pvIndexI = PV('MTEST-PC-BY84-CTA:ser0-Index-I')
    pvEnableI = PV('MTEST-PC-BY84-CTA:ser0-Enable-I')
    pvDataO = PV('MTEST-PC-BY84-CTA:ser0-Data-O')

    # set data
    pvDataI.put(numpy.array(self.data), wait=True)

    # check initial values of outputs
    self.assertEqual(pvDataO.get(), 0)

    # load
    pvLoadI.put(1)
    time.sleep(1)

    # check output
    self.assertEqual(pvDataO.get(), 0)

    # set index
    pvIndexI.put(0)
    time.sleep(1)

    # check output
    self.assertEqual(pvDataO.get(), 0)

    # enable
    pvEnableI.put(1)
    time.sleep(1)

    # check output
    self.assertEqual(pvDataO.get(), 1)

    # disable
    pvEnableI.put(0)
    time.sleep(1)

    # check output
    self.assertEqual(pvDataO.get(), 0)

  def test_play(self):

    self.data = [1, 0, 1, 0, 1, 0, 1, 1]

    print('test_play is running')

    # create PV objects
    pvDataI = PV('MTEST-PC-BY84-CTA:ser0-Data-I')
    pvLoadI = PV('MTEST-PC-BY84-CTA:ser0-Load-I.PROC')
    pvIndexI = PV('MTEST-PC-BY84-CTA:ser0-Index-I')
    pvEnableI = PV('MTEST-PC-BY84-CTA:ser0-Enable-I')
    pvDataO = PV('MTEST-PC-BY84-CTA:ser0-Data-O')

    # set data
    pvDataI.put(numpy.array(self.data), wait=True)

    # check initial values of outputs
    self.assertEqual(pvDataO.get(), 0)

    # load
    pvLoadI.put(1)
    time.sleep(1)

    # check output
    self.assertEqual(pvDataO.get(), 0)

    # enable
    pvEnableI.put(1)
    time.sleep(1)

    # check output
    self.assertEqual(pvDataO.get(), 0)

    # loop over series
    for i in range(len(self.data)):

      # set index
      pvIndexI.put(i)
      time.sleep(1)

      # check output
      self.assertEqual(pvDataO.get(), self.data[i])

    # disable
    pvEnableI.put(0)
    time.sleep(1)

    # check output
    self.assertEqual(pvDataO.get(), 0)

#   # check initial values of outputs
#   self.assertEqual(pvIndex.get(), 0)
#   self.assertEqual(pvIsRunning.get(), 1)
#   self.assertEqual(pvLoad.get(), 0)
#   self.assertEqual(pvSOP.get(), 0)
#   
#   # drive sequence and check
#   for i in range(self.cycles):
#     for k in range(self.length):
#       print('cycle=' + str(i) + ', length=' + str(k))
#       pvSOS.put(i+k)
#       time.sleep(1)
#       self.assertEqual(pvIndex.get(), k)
#       self.assertEqual(pvIsRunning.get(), 1)
#
#   print('dispatching SOS (value=' + str(self.cycles*self.length))
#   pvSOS.put(self.cycles*self.length)
#   time.sleep(1)
#
#   # check final values of outputs
#   self.assertEqual(pvIsRunning.get(), 0)

#    # start series
#    time.sleep(5)
#    pvStart.put(0)
#
#    # drive and check series
#    for i in range(3):
#      for k in range(len(data)):
#        time.sleep(1)
#        pvSOS.put(i+k)
#        time.sleep(1)
#        self.assertEqual(pvO.get(), data[k])


if __name__ == '__main__':
  unittest.main()

