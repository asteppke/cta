import unittest
from epics import PV
import numpy
import time

class TestSeries(unittest.TestCase):

  def test_series(self):

    # define data
    data = [1, 0, 1, 0, 1, 0, 1, 0]

    # create PV objects
    pvI = PV('MTEST-PC-BY84:ctaSeq0Ser0-I')
    pvO = PV('MTEST-PC-BY84:ctaSeq0Ser0-O')
    pvPlay = PV("MTEST-PC-BY84:ctaSeq0Ser0-Load.PROC")
    pvPick = PV("MTEST-PC-BY84:ctaSeq0Ser0-Index")

    # write data to IOC
    pvI.put(numpy.array(data), wait=True)

    # load data to play
    pvPlay.put(1, wait=True)

    # play sequence and verify output
    for i in range(len(data)):
      pvPick.put(i, wait=True)
      time.sleep(1)
      self.assertEqual(pvO.get(), data[i])


  def test_superposition(self):

    # define data
    data = [[0, 1, 0, 1, 0, 1, 0, 1],
            [0, 0, 1, 1, 0, 0, 1, 1],
            [0, 0, 0, 0, 1, 1, 1, 1]]

    # create PV objects
    pvI = [PV('MTEST-PC-BY84:ctaSeq0Ser0-I'), PV('MTEST-PC-BY84:ctaSeq1Ser0-I'), PV('MTEST-PC-BY84:ctaSeq2Ser0-I')]
    pvO = [PV('MTEST-PC-BY84:ctaSeq0Ser0-O'), PV('MTEST-PC-BY84:ctaSeq1Ser0-O'), PV('MTEST-PC-BY84:ctaSeq2Ser0-O')]
    pvPlay = [PV("MTEST-PC-BY84:ctaSeq0Ser0-Load.PROC"), PV("MTEST-PC-BY84:ctaSeq1Ser0-Load.PROC"), PV("MTEST-PC-BY84:ctaSeq2Ser0-Load.PROC")]
    pvPick = [PV("MTEST-PC-BY84:ctaSeq0Ser0-Index"), PV("MTEST-PC-BY84:ctaSeq1Ser0-Index"), PV("MTEST-PC-BY84:ctaSeq2Ser0-Index")]
    pvSupTrg = PV('MTEST-PC-BY84:ctaSupSer0_0.PROC')
    pvSupRes = PV('MTEST-PC-BY84:ctaSupSer0_2')

    # write data to IOC
    for i in range(3):
      pvI[i].put(numpy.array(data[i]), wait=True)

    # load data to play
    for i in range(3):
      pvPlay[i].put(1, wait=True)

    # for each series element
    for i in range(len(data[0])):
      
      # for each sequence
      for k in range(3):

        # pick element
        pvPick[k].put(i, wait=True)

        # check output of series
        self.assertEqual(pvO[k].get(), data[k][i])
        print('output series 0 sequence {0} = '.format(str(k)) + str(pvO[k].get()))

      # trigger superpositon
      pvSupTrg.put(1, wait=True)

      # check result
      self.assertEqual(pvSupRes.get(), data[0][i] or data[1][i] or data[2][i])
      print('superposition series 0 = ' + str(pvSupRes.get()))

    time.sleep(1)

  def test_ctrlSeries(self):

    # define data
    data = [0, 1, 0, 1, 1, 1]

    # create PV objects
    pvI = PV('MTEST-PC-BY84:-I')
    pvO = PV('MTEST-PC-BY84:-O')
    pvLength = PV('MTEST-PC-BY84:Length-I')
    pvCycles = PV('MTEST-PC-BY84:Cycles-I')
    pvStart = PV('MTEST-PC-BY84:Start-I')
    pvStop = PV('MTEST-PC-BY84:Stop-I')
    pvSOS = PV('MTEST-PC-BY84:SOS-I')

    # write series to series
    pvI.put(numpy.array(data), wait=True)

    # configure seqCtrl
    time.sleep(5)
    pvLength.put(6)
    pvCycles.put(3)

    # start series
    time.sleep(5)
    pvStart.put(0)

    # drive and check series
    for i in range(3):
      for k in range(len(data)):
        time.sleep(1)
        pvSOS.put(i+k)
        time.sleep(1)
        self.assertEqual(pvO.get(), data[k])


if __name__ == '__main__':
  unittest.main()

