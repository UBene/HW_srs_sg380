'''
Created on Aug 5, 2014

@author: Frank
'''
from __future__ import division
from ctypes import byref, c_int32, create_string_buffer
import time
import numpy as np
import PyDAQmx as mx

print 'read hardware properties from DAQmx'

#get hardware properties
AIdev = 'X-6368'
buffSize = 2048
chanList = create_string_buffer( buffSize )
devList = create_string_buffer( buffSize )
mx.DAQmxGetSysDevNames(devList, buffSize );
print 'mx devices found ', devList.value
mx.DAQmxGetDevAIPhysicalChans( AIdev, chanList, buffSize )
#print 'physical channels ', chanList.value
maxRate = mx.float64()
mx.DAQmxGetDevAIMaxSingleChanRate( AIdev, mx.byref(maxRate) )
print 'max rate analog input reported', maxRate.value

print 'setup and run task to read  multiple values with callbacks, 1k chunks at 10 kHz'


class CallbackTask(mx.Task):
    def __init__(self):
        mx.Task.__init__(self)
        self.data = np.zeros( 1000, dtype=np.float64 )
        self.a = []
        self.CreateAIVoltageChan('X-6368/ai0', "", mx.DAQmx_Val_Cfg_Default, -10.0, 10.0, mx.DAQmx_Val_Volts, None )
        self.CfgSampClkTiming( "", 10000.0, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 1000 )
        self.AutoRegisterEveryNSamplesEvent( mx.DAQmx_Val_Acquired_Into_Buffer, 1000, 0 )
        self.AutoRegisterDoneEvent( 0 )
        
    def EveryNCallback(self):
        read = c_int32()
        self.ReadAnalogF64( 1000, 10.0, mx.DAQmx_Val_GroupByScanNumber, self.data, 1000, byref(read), None )
        self.a.extend(self.data.tolist())
        print self.data[0]
        return 0 # The function should return an integer
    
    def DoneCallback(self, status):
        print "Task callback on done status:",status.value
        return 0 # The function should return an integer


task=CallbackTask()
task.StartTask()

raw_input('Acquiring samples continuously. Press Enter to interrupt\n')

task.StopTask()
task.ClearTask()

  
print 'task done'

