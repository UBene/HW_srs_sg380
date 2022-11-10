'''
Created on May 2, 2018

@author: Schuck Lab M1
'''
from ctypes import byref, c_uint32, c_int32
import numpy as np

import PyDAQmx
from PyDAQmx import *
from PyDAQmx import DAQmx_Val_Rising, DAQmx_Val_CountUp, DAQmx_Val_ContSamps, DAQmxSetDigEdgeStartTrigSrc
from PyDAQmx import DAQmx_Val_Hz, DAQmx_Val_Low, DAQmx_Val_LargeRng2Ctr, DAQmx_Val_OverwriteUnreadSamps
from PyDAQmx import DAQmx_Val_DMA, DAQmx_Val_HighFreq2Ctr
from PyDAQmx import DAQmx_Val_Volts

from PyDAQmx import Task




###########################################################    
########### Define some functions to use
def read_freq_buffer(task_CT, sample_buffer, SAMPLE_BUFFER_SIZE, _sample_buffer_count  ):
    while True:
        task_CT.ReadCounterF64(
            numSampsPerChan = -1,
            timeout = 0.1,
            readArray = sample_buffer,
            arraySizeInSamps = SAMPLE_BUFFER_SIZE,
            sampsPerChanRead = byref(_sample_buffer_count),
            reserved = None
            )
        if _sample_buffer_count.value > 0:
            break;
    return _sample_buffer_count.value, sample_buffer

def read_average_freq_in_buffer(task_CT, sample_buffer, SAMPLE_BUFFER_SIZE, _sample_buffer_count):
    num_samples, _buffer = read_freq_buffer(task_CT, sample_buffer, SAMPLE_BUFFER_SIZE, _sample_buffer_count)
    result =  np.average(_buffer[:num_samples])
    if np.isnan(result):
        return -1
    else:
        return result
    
def flush_buffer(task_CT, sample_buffer, SAMPLE_BUFFER_SIZE, _sample_buffer_count):
    while True:
        try:
            task_CT.ReadCounterF64(
                numSampsPerChan = SAMPLE_BUFFER_SIZE,
                    timeout = 0,
                    readArray = sample_buffer,
                    arraySizeInSamps = SAMPLE_BUFFER_SIZE,
                    sampsPerChanRead = byref(_sample_buffer_count),
                    reserved = None
                )
            time.sleep(0.0001)
        except:
            break;
        












        
if __name__ == '__main__':
    import time
    #import pylab as pl
    import matplotlib.pyplot as plt
    
    #########
    AO_chan = "/Dev1/ao0"
    counter_chan = "/Dev1/ctr1"
    counter_mode = 'high_freq'
    input_terminal = "/Dev1/PFI0"
    int_t = 0.1 ##integratino time, 
    
    ########Configure AO task
    AO_val = 0.0
    task_AO = Task()
    task_AO.CreateAOVoltageChan(AO_chan, "", -10.0, 10.0, PyDAQmx.DAQmx_Val_Volts, None) #(channel, channel name, min value, max value, units, None)
    
    ########## Configure counter task
    task_CT = Task()
    
    if counter_mode == 'large_range':
        task_CT.CreateCIFreqChan(
            counter = counter_chan ,
            nameToAssignToChannel="",
            minVal = 5e1, # applies measMethod is DAQmx_Val_LargeRng2Ctr
            maxVal = 1e8, # applies measMethod is DAQmx_Val_LargeRng2Ctr
            units = DAQmx_Val_Hz,
            edge = DAQmx_Val_Rising,
            measMethod = DAQmx_Val_LargeRng2Ctr,
            measTime = 0.01, # applies measMethod is DAQmx_Val_HighFreq2Ctr
            divisor = 10, # applies measMethod is DAQmx_Val_LargeRng2Ctr
            customScaleName = None,
            )
    elif counter_mode == 'high_freq':
        task_CT.CreateCIFreqChan(
            counter = counter_chan ,
            nameToAssignToChannel="",
            minVal = 1, # applies measMethod is DAQmx_Val_LargeRng2Ctr
            maxVal = 1e7, # applies measMethod is DAQmx_Val_LargeRng2Ctr
            units = DAQmx_Val_Hz,
            edge = DAQmx_Val_Rising,
            measMethod = DAQmx_Val_HighFreq2Ctr,
            measTime = 0.01, # applies measMethod is DAQmx_Val_HighFreq2Ctr
            divisor = 100, # applies measMethod is DAQmx_Val_LargeRng2Ctr
            customScaleName = None,
            )
    
    ###Specicy input and conuter terminals
    task_CT.SetCIFreqTerm(
        channel = counter_chan,
        data = input_terminal
        )
    ### Set to use continuous sampling
    task_CT.CfgImplicitTiming(
        sampleMode = DAQmx_Val_ContSamps,
        sampsPerChan = 1000)
    
    
    SAMPLE_BUFFER_SIZE = 32768
    _sample_buffer_count = c_int32(0)
    sample_buffer = np.zeros((SAMPLE_BUFFER_SIZE,), dtype=np.float64)  
            
    ############## Start counter to AO conversion
    
    ###Set initial value to zero
    AO_val = 0.0
    AO_scale = 1e-3
    task_AO.StartTask()
    task_AO.WriteAnalogScalarF64(1, 10.0, AO_val, None) #(autostart, timeout, value, reserved for future)
    
    
    t1 = time.time()
    Nacq = 10
    iall = np.arange(0, Nacq)
    cps_all = np.zeros(iall.shape, dtype=float)
    
    for i in iall:
        
        ####### Read in cps value from counter    
        #flush_buffer(task_CT, sample_buffer, SAMPLE_BUFFER_SIZE, _sample_buffer_count  )
        task_CT.StartTask()
        time.sleep(int_t)
        cps = read_average_freq_in_buffer(task_CT, sample_buffer, SAMPLE_BUFFER_SIZE, _sample_buffer_count  )  
        task_CT.StopTask()
        cps_all[i] = cps

        print (i, cps,)
        
        
        ####### convert to voltage value for output
        AO_val = cps*AO_scale
        task_AO.WriteAnalogScalarF64(1, 10.0, AO_val, None) #(autostart, timeout, value, reserved for future)
        
        time.sleep(0.5)

        
    t2 = time.time()
    print ('Average time per data: ', (t2-t1)/Nacq  )  ###Takes about 50ms per data for acuisition
    
    
    
    ####### Stop and cleanup
    
    task_AO.WriteAnalogScalarF64(1, 10.0, 0.0, None)
    task_CT.ClearTask()
    task_AO.StopTask()
    task_AO.ClearTask()


    

    
