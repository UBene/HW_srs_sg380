'''
Created on Aug 5, 2014

@author: Frank
'''
from __future__ import division
import ctypes
import time
import numpy as np

from PyDAQmx import *

print 'NI AO test here - write multiple values 2 channels'

#  c types for DAQmx DLL
AOchan = "X-6368/ao0:1" #two channel output
clockSource = ""

sampleCount = uInt64(10000)

#data = np.zeros((2*sampleCount,), dtype=np.float64 )
data = np.zeros(2*sampleCount.value, dtype=np.float64 )
#dataY = np.zeros((sampleCount,), dtype=np.float64 )
transfer_count = int32()

phase = np.pi * np.linspace(0,3,sampleCount.value )
#chanCount = int32(1)
timeOut = float64( 1.0 )
minVal = -10#float64( -10 )
maxVal = float64( 10 )
daqTrue = bool32( 1 )
daqFalse = bool32( 0 )

clockRate = float64( 100000.0 )
wait = 10

dataX = 10.0 * np.sin( phase )
dataY = 10.0 * np.sin( 3*phase )
data[0:sampleCount.value] = dataX
data[sampleCount.value: ] = dataY

try:
    taskAO = Task()
    
    # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], 
    #    float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
    taskAO.CreateAOVoltageChan( AOchan, "", minVal, maxVal, DAQmx_Val_Volts, "" )
    
    #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
    #                        int32 sampleMode, uInt64 sampsPerChan );
    #  default clock is subsystem acquisition clock
    taskAO.CfgSampClkTiming( "", clockRate, DAQmx_Val_Rising, DAQmx_Val_ContSamps, sampleCount );
   
    #  WriteAnalogF64 (int32 numSampsPerChan, bool32 autoStart, float64 timeout, 
    #    bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved)
    error = taskAO.WriteAnalogF64( sampleCount.value, 0, timeOut,
                       DAQmx_Val_GroupByChannel, data, byref(transfer_count), None )
    print 'Wrote ', sampleCount.value, ' values to ', AOchan, ' transferred ', transfer_count.value

    taskAO.StartTask()
    
    time.sleep(wait)    

    taskAO.StopTask()
    
# except DAQError as err:
#     print "DAQmx Error:", err
    
finally:
    pass

