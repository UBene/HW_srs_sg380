'''
Created on Aug 5, 2014

@author: Frank
'''
from __future__ import division
import ctypes
import time
import numpy as np

import PyDAQmx as mx

print 'NI AO test here - write multiple values 2 channels'

# define waveforms
clockRate = 5e4  #Hz
sampleCount = int( 5e3 )
data = np.zeros(2*sampleCount, dtype=np.float64 )   #buffer
phase = np.pi * np.linspace(0,3,sampleCount )
dataX = 10.0 * np.sin( phase )
dataY = 10.0 * np.sin( 3*phase )
data[0:sampleCount] = dataX
data[sampleCount: ] = dataY
wait = 1.5  #sec

transfer_count = mx.int32()    #pass by ref
clockSource = ""
timeOut = 1.0
minVal = -10
maxVal = 10
autostart = mx.bool32(0)

AOchan = 'X-6368/ao0:1' #two channel output

try:
    taskAO = mx.Task()
    
    # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], 
    #    float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
    taskAO.CreateAOVoltageChan( AOchan, "", minVal, maxVal, mx.DAQmx_Val_Volts, "" )
    
    #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
    #                        int32 sampleMode, uInt64 sampsPerChan );
    #  default clock is subsystem acquisition clock
    taskAO.CfgSampClkTiming( "", clockRate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, sampleCount ) #uInt64( sampleCount ) )
   
    #  WriteAnalogF64 (int32 numSampsPerChan, bool32 autoStart, float64 timeout, 
    #    bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved)
    taskAO.WriteAnalogF64( sampleCount, autostart, timeOut,
                       mx.DAQmx_Val_GroupByChannel, data, mx.byref(transfer_count), None )
    print 'Wrote ', sampleCount, ' values to ', AOchan, ' samples transferred ', transfer_count.value
    taskAO.TaskControl( mx.DAQmx_Val_Task_Commit )
    
    for i in range(4):
        print 'task ready...'      
        taskAO.StopTask()   #task must be stopped before starting, does not 'autostop' except with retrigger option set for ext trigger
        taskAO.StartTask()
        time.sleep(wait)        
        print 'loop'
#       time.sleep(wait)    
        
# except DAQError as err:
#     print "DAQmx Error:", err
    
finally:
    print 'task done'

