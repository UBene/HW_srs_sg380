from __future__ import division, absolute_import, print_function
from ctypes import byref, c_uint32, c_int32
import numpy as np

import PyDAQmx
import PyDAQmx as mx
from PyDAQmx import DAQmx_Val_Rising, DAQmx_Val_CountUp, DAQmx_Val_ContSamps, DAQmxSetDigEdgeStartTrigSrc
from PyDAQmx import DAQmx_Val_Hz, DAQmx_Val_Low, DAQmx_Val_LargeRng2Ctr, DAQmx_Val_OverwriteUnreadSamps
from PyDAQmx import DAQmx_Val_DMA, DAQmx_Val_HighFreq2Ctr, DAQmx_Val_LowFreq1Ctr

import time
import logging
logger = logging.getLogger(__name__)


SAMPLE_BUFFER_SIZE = 32000

class NI_FreqCounter(object):
    """ National Instruments DAQmx interface to a frequency counter
        Tested on an X-series PCIe DAQ card
    """
    
    def __init__(self, counter_chan="Dev1/ctr0", input_terminal = "/Dev1/PFI0", mode = "large_range", debug=False):
    
        self.counter_chan = counter_chan
        self.input_terminal = input_terminal
        self.debug = debug
        self.mode = mode
    
        assert mode in ['large_range', 'high_freq', 'low_freq']
        
        self.create_task()
    
    def create_task(self):
    
        # need to check if task exists and fail
    
        #self.task = PyDAQmx.Task()
        self.task_handle = mx.TaskHandle(0)
        mx.DAQmxCreateTask("",byref(self.task_handle))
        
        if self.mode == 'large_range':
            logger.debug( 'counter_chan {}'.format( self.counter_chan))
            logger.debug( 'input_terminal {}'.format( self.input_terminal))
            
            mx.DAQmxCreateCIFreqChan(self.task_handle,
                counter = str(self.counter_chan) ,
                nameToAssignToChannel="",
                minVal = 5e1, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                maxVal = 1e8, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                units = DAQmx_Val_Hz,
                edge = DAQmx_Val_Rising,
                measMethod = DAQmx_Val_LargeRng2Ctr,
                measTime = 1.0, # applies measMethod is DAQmx_Val_HighFreq2Ctr
                divisor = 100, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                customScaleName = None,
                )
        elif self.mode == 'high_freq':
            mx.DAQmxCreateCIFreqChan(self.task_handle,
                counter = self.counter_chan ,
                nameToAssignToChannel="",
                minVal = 1e1, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                maxVal = 1e7, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                units = DAQmx_Val_Hz,
                edge = DAQmx_Val_Rising,
                measMethod = DAQmx_Val_HighFreq2Ctr,
                measTime = 0.05, # applies measMethod is DAQmx_Val_HighFreq2Ctr
                divisor = 100, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                customScaleName = None,
                )
        elif self.mode == 'low_freq':
            mx.DAQmxCreateCIFreqChan(self.task_handle,
                counter = self.counter_chan ,
                nameToAssignToChannel="",
                minVal = 1e1, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                maxVal = 1e7, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                units = DAQmx_Val_Hz,
                edge = DAQmx_Val_Rising,
                measMethod = DAQmx_Val_LowFreq1Ctr,
                measTime = 0.05, # applies measMethod is DAQmx_Val_HighFreq2Ctr
                divisor = 100, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                customScaleName = None,
                )
        
        ### data = c_int32(0)
        ### self.task.GetCIDataXferMech(channel=self.counter_chan, data=data )
        ### print "XFmethod" , data.value
        
        # set DMA
        #self.task.SetCIDataXferMech(channel=self.counter_chan, data=DAQmx_Val_DMA)
        
        ### self.task.GetReadOverWrite(data=byref(data))
        ### print "overwrite", data.value
        
        #Set the input terminal of the counter
        mx.DAQmxSetCIFreqTerm(self.task_handle,
            channel = self.counter_chan,
            data = self.input_terminal)

        #Set the counter channel to continuously sample into a buffer.  The size of the
        #buffer is set by sampsPerChan.
        mx.DAQmxCfgImplicitTiming(self.task_handle,
            sampleMode = DAQmx_Val_ContSamps,
            sampsPerChan = 1000)
            
        
        mx.DAQmxSetReadOverWrite(self.task_handle, DAQmx_Val_OverwriteUnreadSamps)

        ### self.task.GetReadOverWrite(data=byref(data))
        ### print "overwrite", data.value
            
        # Sample buffer
        self._sample_buffer_count = c_int32(0)
        self.sample_buffer = np.zeros((SAMPLE_BUFFER_SIZE,), dtype=np.float64)

    
    def start(self):
        status = mx.DAQmxStartTask(self.task_handle)
        logger.debug( 'start status {}'.format( status ))
    
    def stop(self):
        status = mx.DAQmxStopTask(self.task_handle)
        logger.debug( 'stop status {}'.format( status ))

    
    def reset(self):
        status = mx.DAQmxStopTask(self.task_handle)
        status = mx.DAQmxClearTask(self.task_handle)
        self.create_task()
        self.start()

    def read_freq_buffer(self):
        status = \
        mx.DAQmxReadCounterF64(self.task_handle,
            numSampsPerChan = -1,
            timeout = 0.1, ###
            readArray = self.sample_buffer,
            arraySizeInSamps = SAMPLE_BUFFER_SIZE,
            sampsPerChanRead = byref(self._sample_buffer_count),
            reserved = None
            )
        if self.debug: logger.debug( 'read_freq_buffer {} {} {}'.format( status, self._sample_buffer_count, np.max(self.sample_buffer)))
        return self._sample_buffer_count.value, self.sample_buffer

    def read_average_freq_in_buffer(self):
        num_samples, _buffer = self.read_freq_buffer()
        if self.debug: logger.debug("read_average_freq_in_buffer {} {}".format( num_samples, _buffer))
        #logger.warning("read_average_freq_in_buffer {} {} {}".format( num_samples, _buffer, np.nonzero(_buffer)))
        if num_samples == 0:
            return 0
        result =  np.average(_buffer[:num_samples])
        if np.isnan(result):
            return -1
        else:
            return result

    def close(self):
        if hasattr(self,'task'):
            self.task.StopTask()
            self.task.ClearTask()
    
    def __exit__(self, type_, value, traceback):
        self.close()
        return False
        
    def __enter__(self):
        return self
        
if __name__ == '__main__':
    import time
    
    with NI_FreqCounter(debug=True) as fc:

        for i in range(10):
            fc.start()
            time.sleep(0.1)
            hz = fc.read_average_freq_in_buffer()
            fc.stop()
            print("%i: %e Hz" % (i, hz))
