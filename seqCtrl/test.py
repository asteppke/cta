import unittest
from epics import PV
import numpy
import time
from subprocess import Popen, DEVNULL

class TestSeqCtrl(unittest.TestCase):

  #def setUp(self):
    #self.process = Popen(['iocsh', 'seqCtrl/startup.script_test_seqCtrl'], stdout=DEVNULL, stderr=DEVNULL)
    #time.sleep(5)

  #def tearDown(self):
    #self.process.terminate()

  def test_basic(self):

    self.length = 3
    self.cycles = 2

    print('test_basic is running')

    # create PV objects
    pvLength = PV('MTEST-PC-BY84-CTA:seq0Ctrl-Length-I')
    pvCycles = PV('MTEST-PC-BY84-CTA:seq0Ctrl-Cycles-I')
    pvStart = PV('MTEST-PC-BY84-CTA:seq0Ctrl-Start-I')
    pvStop = PV('MTEST-PC-BY84-CTA:seq0Ctrl-Stop-I')
    pvSOS = PV('MTEST-PC-BY84-CTA:seq0Ctrl-SOS-I')
    pvIndex = PV('MTEST-PC-BY84-CTA:seq0Ctrl-Index-O')
    pvIsRunning = PV('MTEST-PC-BY84-CTA:seq0Ctrl-IsRunning-O')
    pvLoad = PV('MTEST-PC-BY84-CTA:seq0Ctrl-Load_')
    pvSOP = PV('MTEST-PC-BY84-CTA:seq0Ctrl-SOP_')

    # check initial values of outputs
    self.assertEqual(pvIndex.get(), 0)
    self.assertEqual(pvIsRunning.get(), 0)
    self.assertEqual(pvLoad.get(), 0)
    self.assertEqual(pvSOP.get(), 0)

    # configure seqCtrl
    pvLength.put(self.length)
    pvCycles.put(self.cycles)

    # start sequence
    pvStart.put(0)
    time.sleep(1)

    # check initial values of outputs
    self.assertEqual(pvIndex.get(), 0)
    self.assertEqual(pvIsRunning.get(), 1)
    self.assertEqual(pvLoad.get(), 0)
    self.assertEqual(pvSOP.get(), 0)
    
    # drive sequence and check
    for i in range(self.cycles):
      for k in range(self.length):
        print('cycle=' + str(i) + ', length=' + str(k))
        pvSOS.put(i+k)
        time.sleep(1)
        self.assertEqual(pvIndex.get(), k)

    # check final values of outputs
    self.assertEqual(pvIndex.get(), 0)
    self.assertEqual(pvIsRunning.get(), 0)
    self.assertEqual(pvLoad.get(), 0)
    self.assertEqual(pvSOP.get(), 0)

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

