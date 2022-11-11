from __future__ import division
import ctypes

import time
from pipython import GCSDevice, pitools
import os
import platform
import numpy as np
# from _pytest.skipping import _get_pos
from dis import dis

SLOW_STEP_PERIOD = 0.20  # units are seconds


class PINanopositioner(object):

    def __init__(self, debug=False):
        self.debug = debug

        CONTROLLERNAME = 'E-727'
        refmode = None
        deviceaxes = ('1', '2', '3')
        self.num_axes = 3
        self.sleeptime = 0.01  # sleep time: 0.01 sec / (um /sec)
        self.pidevice = GCSDevice()
        ID = self.pidevice.EnumerateUSB(CONTROLLERNAME)

        self.pidevice.ConnectUSB(ID[0])

        if self.debug: print("Device ID: ", ID)

        if not ID:
            print("PINanopositioner failed to grab device handle ", ID)

        if self.debug: print('connected: {}'.format(self.pidevice.qIDN().strip()))

        #######################################################
        if self.pidevice.HasINI():
            self.pidevice.INI()
        if self.pidevice.HasONL():
            self.pidevice.ONL(deviceaxes, [True] * 3)
        pitools.stopall(self.pidevice)
        self.pidevice.SVO(deviceaxes, (True, True, True))
        self.pidevice.VCO(('1', '2', '3'), (False, False, False))
        pitools.waitontarget(self.pidevice, axes=deviceaxes)

        self.cal = list(self.pidevice.qTMX().values())
        # print("index self.cal", self.cal[0], self.cal[1], self.cal[2])
        print("self.cal", self.cal)
        self.cal_X = self.cal[0]
        self.cal_Y = self.cal[1]
        self.cal_Z = self.cal[2]
        print(self.cal_X, self.cal_Y, self.cal_Z)
        #################################################

    def readwavedata(self, DATAFILE):
        """Read DATAFILE, must have a column for each wavetable.
        @return : Datapoints as list of lists of values.
        """
        print('read wave points from file {}'.format(DATAFILE))
        data = None
        with open(DATAFILE, 'r') as datafile:
            for line in datafile:
                items = line.strip().split()
                if data is None:
                    print('found {} data columns in file'.format(len(items)))
                    data = [[] for _ in range(len(items))]
                for i in range(len(items)):
                    data[i].append(items[i])
        return data


if __name__ == '__main__':
    print("PI nanopositioner test")

    NUMCYLES = [1, 1, 1]  # number of cycles for wave generator output
    TABLERATE = 32  # duration of a wave table point = servo cycle time * tablerate (default servo cycle time = 50us)
    DATAFILE = 'PNT_test.txt'

    nanodrive = PINanopositioner(debug=True)
    print(len(nanodrive.pidevice.axes[:2]))

    wavedata = nanodrive.readwavedata(DATAFILE)
    # print(len(wavedata))

    axes = nanodrive.pidevice.axes[:len(wavedata)]
    assert len(wavedata) == len(axes), 'this sample requires {} connected axes'.format(len(wavedata))
    wavetables = (1, 2, 3)
    # print(wavetables)
    wavegens = (1, 2, 3)
    if nanodrive.pidevice.HasWCL():  # you can remove this code block if your controller does not support WCL()
        print('clear wave tables {}'.format(wavetables))
        nanodrive.pidevice.WCL(wavetables)
    for i, wavetable in enumerate(wavetables):
        print('write wave points of wave table {} and axis {}'.format(wavetable, axes[i]))
        pitools.writewavepoints(nanodrive.pidevice, wavetable, wavedata[i], bunchsize=10)
    if nanodrive.pidevice.HasWSL():  # you can remove this code block if your controller does not support WSL()
        print('connect wave tables {} to wave generators {}'.format(wavetables, wavegens))
        nanodrive.pidevice.WSL(wavegens, wavetables)
    if nanodrive.pidevice.HasWGC():  # you can remove this code block if your controller does not support WGC()
        print('set wave generators {} to run for {} cycles'.format(wavegens, NUMCYLES))
        nanodrive.pidevice.WGC(wavegens, NUMCYLES)
    if nanodrive.pidevice.HasWTR():  # you can remove this code block if your controller does not support WTR()
        print('set wave table rate to {} for wave generators {}'.format(TABLERATE, wavegens))
        nanodrive.pidevice.WTR(0, [TABLERATE], 0)
    startpos = [wavedata[i][0] for i in range(len(wavedata))]
    print('move axes {} to start positions {}'.format(axes, startpos))
    nanodrive.pidevice.MOV(axes, startpos)
    pitools.waitontarget(nanodrive.pidevice, axes)
    time.sleep(2.0)
    print('start wave generators {}'.format(wavegens))
    nanodrive.pidevice.WOS(('1', '2', '3'), (0.0, 0.0, 0.0))  # Set wavegenerator level offset
    nanodrive.pidevice.WGO(wavegens, mode=[257] * len(wavegens)) # code 257 means start at end position
    pitools.waitontarget(nanodrive.pidevice, axes)
    while any(list(nanodrive.pidevice.IsGeneratorRunning(wavegens).values())):
        print(nanodrive.pidevice.qPOS(('1', '2', '3'))),
        time.sleep(1.0)

    print('\nreset wave generators {}'.format(wavegens))
    print(nanodrive.pidevice.qPOS(('1', '2', '3')))
    # nanodrive.pidevice.WGO(wavegens, mode=[0] * len(wavegens))
    nanodrive.pidevice.STP(noraise = True)

    print('\nrun 2')

    nanodrive.pidevice.WOS(('1', '2', '3'), (20, 20, 0.0))  # Set wavegenerator level offset
    nanodrive.pidevice.WGO(wavegens, mode=[257] * len(wavegens))  # code 257 means start at end position
    pitools.waitontarget(nanodrive.pidevice, axes)
    while any(list(nanodrive.pidevice.IsGeneratorRunning(wavegens).values())):
        print(nanodrive.pidevice.qPOS(('1', '2', '3'))),
        time.sleep(1.0)

    print('\nreset wave generators {}'.format(wavegens))
    print(nanodrive.pidevice.qPOS(('1', '2', '3')))
    # nanodrive.pidevice.WGO(wavegens, mode=[0] * len(wavegens))
    nanodrive.pidevice.STP(noraise=True)
    print('done')

    print('done')