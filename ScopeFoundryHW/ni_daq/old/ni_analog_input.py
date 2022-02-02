import numpy as np
import PyDAQmx
import ctypes
from ctypes import byref, c_uint32, c_int32, c_double

SAMPLE_BUFFER_SIZE = 32768*4

class NI_AnalogInput(object):

    def __init__(self, input_channel = "Dev1/ao0", debug=False):
    
        self.input_terminal = input_channel
        self.debug = debug
    
        self.create_task()

    def create_task(self):
    
        # need to check if task exists and fail

        # Create Task
        self.task = PyDAQmx.Task()


        # Configure Task
        self.task.CreateAIVoltageChan(
                      physicalChannel = self.input_terminal,
                      nameToAssignToChannel = "",
                      terminalConfig = PyDAQmx.DAQmx_Val_Cfg_Default,
                      minVal = -10.0,
                      maxVal = +10.0,
                      units = PyDAQmx.DAQmx_Val_Volts,
                      customScaleName = "",
                      )

        # for sending an array of data
        self.task.CfgSampClkTiming(
                      source="",
                      rate=100000.0, # Hz
                      activeEdge = PyDAQmx.DAQmx_Val_Rising ,
                      sampleMode = PyDAQmx.DAQmx_Val_ContSamps,
                      sampsPerChan = 1000 ,
                      )
        
        self.task.SetReadOverWrite(PyDAQmx.DAQmx_Val_OverwriteUnreadSamps)
        self.task.SetReadRelativeTo(PyDAQmx.DAQmx_Val_MostRecentSamp)
        data = c_int32(0)
        self.task.GetReadOffset(byref(data))
        print "ReadOffset", data.value
        
        self._sample_buffer_count = c_int32(0)
        self.sample_buffer = np.zeros((SAMPLE_BUFFER_SIZE,), dtype=np.float64)
        
        
    def start(self):
        self.task.StartTask()
    
    def stop(self):
        self.task.StopTask()
    
    def reset(self):
        self.task.StopTask()
        self.task.ClearTask()
        self.create_task()
        self.start()

    def read_voltage_buffer(self):
        #DAQmxErrChk (DAQmxReadAnalogF64(taskHandle,1000,10.0,DAQmx_Val_GroupByChannel,data,1000,&read,NULL));
        self.task.ReadAnalogF64(
                        numSampsPerChan = -1,
                        timeout = 2.0,
                        fillMode = PyDAQmx.DAQmx_Val_GroupByChannel,
                        readArray = self.sample_buffer, # output array
                        arraySizeInSamps = SAMPLE_BUFFER_SIZE,
                        sampsPerChanRead = byref(self._sample_buffer_count),
                        reserved = None
                        )
        
        return self._sample_buffer_count.value, self.sample_buffer

    def read_average_voltage_in_buffer(self):
        num_samples, _buffer = self.read_voltage_buffer()
        if self.debug: print num_samples, _buffer
        result =  np.average(_buffer[:num_samples])
        if np.isnan(result):
            return -1
        else:
            return result
        
    def read_voltage_single(self):
        val = c_double()
        self.task.ReadAnalogScalarF64(timeout = 0.1, value = byref(val), reserved = None) 
        return val.value

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
    
    with NI_AnalogInput(input_channel="ADC_BNC/ai0", debug=True) as ain:

        t0 = time.time()
        for i in range(10):
            #ain.start()
            #time.sleep(1)
            #vread = ain.read_average_voltage_in_buffer()
            vread = ain.read_voltage_single()
            #ain.stop()

            print "%g seconds elapsed %i: %e V" % (time.time()-t0, i, vread)
            t0 = time.time()

