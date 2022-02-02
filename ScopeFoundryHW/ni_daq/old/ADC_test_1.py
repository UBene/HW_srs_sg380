'''
Created on Jul 29, 2014

@author: Frank
'''

from PyDAQmx.DAQmxTypes import *
from PyDAQmx.DAQmxConstants import *
from PyDAQmx.DAQmxFunctions import *
from PyDAQmx.Task import Task

import ctypes
import time
import numpy as np

analog_input = Task()
read = int32()
loop_count = 10
sample_count = int(1e4)
data = np.zeros((sample_count,loop_count), dtype=np.float64)
delta = np.zeros(loop_count)

rate_100k = 1.0e5
# DAQmx Configure Code
analog_input.CreateAIVoltageChan("ADC_BNC/ai0","",DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None)
analog_input.CfgSampClkTiming("",rate_100k,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,sample_count)

status = c_uint32()
analog_input.GetReadAutoStart(byref(status))
print 'autostart status is', status
#analog_input.StartTask()    # DAQmx Start Code

for j in range(4):
    print j
    start = time.clock()
    for i in range(loop_count):
    
        # DAQmx Read Code
        #analog_input.ReadAnalogF64(-1,10.0,DAQmx_Val_GroupByChannel,data,1000,byref(read),None)
        #print "Acquired {} points mean {}".format( read.value, data.mean() )
        analog_input.ReadAnalogF64(-1,10.0,DAQmx_Val_GroupByChannel,data[:,i],sample_count,byref(read),None)
        delta[i] = time.clock()
    
#     for i in range(1,loop_count):
#         delta[i] = delta[i] - delta[i-1]
#     delta[0] -= start
#     
    for i in range(loop_count):
        print "mean {} elapsed {} ".format( data[:,i].mean(), delta[i] )
print 'done'

if __name__ == '__main__':
    pass