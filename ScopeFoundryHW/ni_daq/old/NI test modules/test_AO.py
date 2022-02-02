'''
Created on Aug 5, 2014

@author: Frank
'''
import ctypes
import time
import numpy as np

import PyDAQmx as mx

print 'NI AO test here - write single values inside loops'

#  c types for DAQmx DLL
AOchan = "X-6368/ao0:1"

data0 = np.zeros(2, dtype=np.float64)
data1 = np.zeros(2, dtype=np.float64)
transfer_count = mx.int32()
sampleCount = 1
timeOut = 1.0
minVal = -10
maxVal = 10
autoStart = mx.bool32( 0 )

data0[0] = data1[1] = 0.5
wait = 0.001

try:
    taskAO = mx.Task()
    
    # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], 
    #    float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
    taskAO.CreateAOVoltageChan( AOchan, "", minVal, maxVal, mx.DAQmx_Val_Volts, "" )
    #taskAO.TaskControl(mx.DAQmx_Val_Task_Commit )
    taskAO.TaskControl(mx.DAQmx_Val_Task_Start )
    
    #  WriteAnalogF64 (int32 numSampsPerChan, bool32 autoStart, float64 timeout, 
    #    bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved)
    elapsed = 0
    count = 1000
    time.clock();
    for x in range(count):
        taskAO.WriteAnalogF64( sampleCount, autoStart, timeOut,
                               mx.DAQmx_Val_GroupByChannel, data0, mx.byref(transfer_count), None )
        #time.sleep(wait)
        taskAO.WriteAnalogF64( sampleCount, autoStart, timeOut,
                               mx.DAQmx_Val_GroupByChannel, data1, mx.byref(transfer_count), None )
        #time.sleep(wait)
        #elapsed += 2*wait
    elapsed = time.clock()
    count *= 2
    print "overhead per step {} for {} steps".format( elapsed / count, count )
    
# except DAQError as err:
#     print "DAQmx Error: %s" %err
finally:
    pass

