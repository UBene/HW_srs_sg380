'''
Created on Feb 4, 2016
Created on Aug 5, 2014

@author: Frank
'''
import ctypes
import time
import numpy as np

import PyDAQmx as mx

print 'NI A1 test here - read single values inside loops'

from equipment.NI_Daq import Adc

#  c types for DAQmx DLL
AIchan = "X-6368/ai1"

#data0 = np.zeros(2, dtype=np.float64)
#data1 = np.zeros(2, dtype=np.float64)
transfer_count = mx.int32()
sampleCount = 1
timeOut = 1.0
minVal = -10
maxVal = 10
autoStart = mx.bool32( 0 )

wait = 0.001


adc = Adc(channel=AIchan, range = 10.0, name = '', terminalConfig='default')
adc.start()

elapsed = 0
count = 1000

data = np.zeros(count, dtype=float)

time.clock()
for x in range(count):
    data[x] = adc.get()
elapsed = time.clock()
print "overhead per step {} for {} steps".format( elapsed / count, count )
print "data mean {} std {}".format(data.mean(),np.std(data)) 
