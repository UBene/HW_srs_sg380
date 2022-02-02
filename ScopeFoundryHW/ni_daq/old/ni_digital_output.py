from ctypes import byref, c_uint32, c_int32
import numpy as np

import PyDAQmx

from PyDAQmx import DAQmx_Val_ChanForAllLines, DAQmx_Val_GroupByChannel

class NI_DigitalOutput(object):
    """ National Instruments DAQmx interface to 8 Digital output channels
        Based on NI C example WriteDigChan.c
        Tested on an X-series PCIe DAQ card
    """
    
    def __init__(self, output_terminal = "Dev1/port0/line0:7", debug=False):
    
        self.input_terminal = input_terminal
        self.debug = debug
    
    	self.create_task()

    def create_task(self):
    
    	# need to check if task exists and fail
    
        self.task = PyDAQmx.Task()

        self.task.CreateDOChan(
            lines = self.output_terminal,
            nameToAssignToLines = "",
            lineGrouping = DAQmx_Val_ChanForAllLines)
            
    def start(self):
    	self.task.StartTask()
    
    def stop(self):
    	self.task.StopTask()
    
    def reset(self):
    	self.task.StopTask()
    	self.task.ClearTask()
    	self.create_task()
    	self.start()

    def write_data(self, data):
    
        self.data = np.array(data[:7], dtype=np.uint8)
    
        self.task.WriteDigitalLines(
            numSampsPerChan=1,
            autoStart=1,
            timeout=10.0,
            dataLayout=DAQmx_Val_GroupByChannel,
            write_array=data, #uint8 array
            sampsPerChanWritten=None, # output for buffered writes
            reserved=None)

    def close(self):
        if hasattr(self,'task'):
            self.task.StopTask()
            self.task.ClearTask()
    
    def __exit__(self, type, value, traceback):
        self.close()
        return False
        
    def __enter__(self):
        return self

if __name__ == '__main__':
    import time

    with NI_DigitalOutput(debug=True) as dout:
        
        dout.start()
        dout.write_data( [0,1,0,1,0,1,0,1] )
        
    