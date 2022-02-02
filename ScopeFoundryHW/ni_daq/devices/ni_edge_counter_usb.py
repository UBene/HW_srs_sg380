from ctypes import byref, c_uint32, c_int32
import numpy as np

import time

import PyDAQmx
from PyDAQmx import DAQmx_Val_Rising, DAQmx_Val_CountUp, DAQmx_Val_ContSamps, DAQmxSetDigEdgeStartTrigSrc
from PyDAQmx import DAQmx_Val_Hz, DAQmx_Val_Low, DAQmx_Val_LargeRng2Ctr, DAQmx_Val_OverwriteUnreadSamps
from PyDAQmx import DAQmx_Val_DMA, DAQmx_Val_HighFreq2Ctr, DAQmx_Val_FiniteSamps


SAMPLE_BUFFER_SIZE = 32768

class NI_EdgeCounterUSB(object):
    """ National Instruments DAQmx interface to a frequency counter
        Adapted to work with USD DAQ cards
    """
    
    def __init__(self, counter_chan="Dev1/ctr1", input_terminal = "/Dev1/PFI0", mode = "large_range", 
                 count_duration = 0.01, debug=False):
    
        self.counter_chan = counter_chan
        self.input_terminal = input_terminal
        self.debug = debug
        self.mode = mode
        self.count_duration = count_duration
    
        assert mode in ['large_range', 'high_freq']
        assert count_duration > 0

        self.create_task()

    def create_task(self):
    
        # need to check if task exists and fail
    
        # Sample clock task defines the sampling frequency using the clock on the DAQ card.   
        self.sample_clock = PyDAQmx.Task()
        self.sample_clock .CreateCOPulseChanFreq(
                counter="Dev1/ctr1",
                nameToAssignToChannel="sampleClock",
                units=DAQmx_Val_Hz,
                idleState=DAQmx_Val_Low,
                initialDelay = 0,
                freq = 4/self.count_duration,
                dutyCycle = 0.50
                )
        self.sample_clock .CfgImplicitTiming(
            sampleMode = DAQmx_Val_ContSamps,
            sampsPerChan = 0
        )
        
        
        # Counter is the DAQ task for counting edges
        self.counter = PyDAQmx.Task()
        self.counter.CreateCICountEdgesChan(
            counter='Dev1/ctr0',
            nameToAssignToChannel="edgeCounter",
            edge=DAQmx_Val_Rising,
            initialCount=0,
            countDirection=DAQmx_Val_CountUp
        )
               
        # Set the counter times to use the sample clock
        self.counter.CfgSampClkTiming(source = '/Dev1/PFI5',
             rate = 4/self.count_duration, 
             activeEdge = DAQmx_Val_Rising, 
             sampleMode = DAQmx_Val_FiniteSamps, 
             sampsPerChan = 4
        )

        # Okay to have sample clock running.
        self.sample_clock.StartTask()
        
        # Allocate the buffer
        self.data_buffer = np.zeros(4, dtype=np.uint32)
        
    
    def set_sample_time(self, new_sample_time):
        assert new_sample_time > 0 
        self.sample_time = new_sample_time
        self.reset()
    
    def set_total_sample_count(self, new_total_sample_count):
        assert new_total_sample_count > 0
        self.total_sample_count = new_total_sample_count
        
    
    def reset(self):
        self.sample_clock.StopTask()
        self.create_task()

    
    def read_counts(self):
        
        self.counter.StartTask()
        
        samples_read_count = c_int32(0)
       
        self.counter.ReadCounterU32(
            numSampsPerChan = -1,
            timeout = self.count_duration,
            readArray = self.data_buffer,
            arraySizeInSamps = 4096,
            sampsPerChanRead = byref(samples_read_count),
            reserved = None
        )
        
        self.counter.StopTask()
        
        assert samples_read_count != 4
        return np.sum(self.data_buffer)
            

    def close(self):
        if hasattr(self,'task'):
            self.sample_clock.StopTask()
            self.sample_clock.ClearTask()
            
            self.counter.StopTask()
            self.counter.ClearTask()
    
    def __exit__(self, type_, value, traceback):
        self.close()
        return False
        
    def __enter__(self):
        return self
        
if __name__ == '__main__':
    import time
    
    with NI_EdgeCounterUSB(debug=True, count_duration=0.05) as fc:

        for i in range(10):
            t1 = time.time()
            cts = fc.read_counts()
            t2 = time.time()
            print cts/fc.count_duration, t2-t1
