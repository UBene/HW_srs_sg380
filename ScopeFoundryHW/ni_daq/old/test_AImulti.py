'''
Created on Aug 5, 2014

@author: Frank
'''
from __future__ import division
import ctypes
import time
import numpy as np

import PyDAQmx as mx

print 'NI Analog input test here - read  multiple values 1 channel'

AIdev = 'X-6368'
buffSize = 2048
chanList = ctypes.create_string_buffer( buffSize )
mx.DAQmxGetDevAIPhysicalChans( AIdev, chanList, buffSize )
#print 'physical channels ', chanList.value
maxRate = mx.float64()
mx.DAQmxGetDevAIMaxSingleChanRate( AIdev, mx.byref(maxRate) )
print 'max rate ', maxRate.value

# define waveforms
clockRate = maxRate.value  #Hz
acqTime = 0.01
loopCount = 50
sampleCount = int( acqTime * clockRate )
#print 'sample count ', sampleCount

data = np.zeros(sampleCount, dtype=np.float64 )   #buffer

transfer_count = mx.int32()    #pass by ref
clockSource = ""
timeOut = 1.0
minVal = -10
maxVal = 10

AIchan = 'X-6368/ai0' #two channel output

try:
    taskAI = mx.Task()
    #  CreateAIVoltageChan (const char physicalChannel[], const char nameToAssignToChannel[], int32 terminalConfig, 
    #                        float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);

    taskAI.CreateAIVoltageChan( AIchan, "", mx.DAQmx_Val_Cfg_Default, minVal, maxVal, mx.DAQmx_Val_Volts, None )
   
    #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
    #                        int32 sampleMode, uInt64 sampsPerChan );
    #  default clock is subsystem acquisition clock
    taskAI.CfgSampClkTiming( "", clockRate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, mx.uInt64( sampleCount ) ) 


    #check speed
    for i in range(5):   
        #  ReadAnalogF64 ( int32 numSampsPerChan, float64 timeout, bool32 fillMode, 
        #        float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved)
        taskAI.ReadAnalogF64( sampleCount, timeOut, mx.DAQmx_Val_GroupByChannel, 
                              data, sampleCount, mx.byref(transfer_count), None )
        print np.mean(data)
    
    taskAI.StopTask()
    start = time.clock()
    for i in range(loopCount):   
        taskAI.StartTask()
        taskAI.ReadAnalogF64( sampleCount, timeOut, mx.DAQmx_Val_GroupByChannel, 
                              data, sampleCount, mx.byref(transfer_count), None )
        taskAI.StopTask()
    elapsed = time.clock() - start
    print loopCount, ' samples of ', acqTime, 'sec at', clockRate, 'Hz in ', elapsed, 'sec, finite overhead ', elapsed - acqTime * loopCount
    
    taskAI.StopTask()
    taskAI.CfgSampClkTiming( "", clockRate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, mx.uInt64( sampleCount ) )
    taskAI.TaskControl( mx.DAQmx_Val_Task_Commit )
    start = time.clock()
    for i in range(loopCount):   
        taskAI.ReadAnalogF64( sampleCount, timeOut, mx.DAQmx_Val_GroupByChannel, 
                              data, sampleCount, mx.byref(transfer_count), None )
    elapsed = time.clock() - start
    print loopCount, ' samples of ', acqTime, 'sec at', clockRate, 'Hz in ', elapsed, 'sec, continuous overhead ', elapsed - acqTime * loopCount
    
#    time.sleep(2)
#     print 'wait and read'
#     taskAI.DAQmxSetReadRelativeTo( mx.DAQmx_Val_MostRecentSamp );
# #     try:
# #         taskAI.ReadAnalogF64( sampleCount, timeOut, mx.DAQmx_Val_GroupByChannel, 
# #                               data, sampleCount, mx.byref(transfer_count), None )
# #     except mx.DAQError as err:
# #         pass
#     taskAI.ReadAnalogF64( sampleCount, timeOut, mx.DAQmx_Val_GroupByChannel, 
#                               data, sampleCount, mx.byref(transfer_count), None )
#     print 'after flush ', np.mean( data )

# except DAQError as err:
#     print "DAQmx Error:", err
    
finally:
    print 'task done'

