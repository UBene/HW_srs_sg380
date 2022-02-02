#ni_analog_output

import numpy as np
import PyDAQmx
import ctypes

#from PyDAQmx import DAQmx_Val_Volts, DAQmx_Val_Rising, DAQmx_Val_ContSamps

#DAQmx_Val_Volts

class NI_AnalogOutput(object):
    """
    Based on ContGen-IntClk.c from AO category
    and VoltUpdate.c
    """
    
    def __init__(self, output_channel = "Dev1/ao0", debug=False):
    
        self.output_terminal = output_channel
        self.debug = debug
    
        self.create_task()

    def create_task(self):
    
        # need to check if task exists and fail

        # Create Task
        self.task = PyDAQmx.Task()


        # Configure Task
        self.task.CreateAOVoltageChan(
                      physicalChannel = self.output_terminal,
                      nameToAssignToChannel = "",
                      minVal = -10.0,
                      maxVal = +10.0,
                      units = PyDAQmx.DAQmx_Val_Volts,
                      customScaleName = "",
                      )
        
        # for sending an array of data
        """self.task.CfgSampClkTiming(
                      source="",
                      rate=1000.0,
                      activeEdge = PyDAQmx.DAQmx_Val_Rising ,
                      sampleMode = PyDAQmx.DAQmx_Val_ContSamps ,
                      sampsPerChanToAcquire = 1000 ,
                      )
        
        #DAQmxRegisterDoneEvent #    DAQmxErrChk (DAQmxRegisterDoneEvent(taskHandle,0,DoneCallback,NULL));
        
        # write data
        
        sampsPerChanWritten = ctypes.c_int32
        
        self.task.WriteAnalogF64(
                         numSampsPerChan = 1000,
                         autoStart = False,
                         timeout = 10.0,
                         dataLayout = PyDAQmx.DAQmx_Val_GroupByChannel,
                         writeArray = data,
                         reserved = None,
                         sampsPerChanWritten = byref(sampsPerChanWritten)
                         )
                
        
        """
        
        def write_single_volt(self, volt):
            self.task.WriteAnalogF64(
                         numSampsPerChan = 1,
                         autoStart = True,
                         timeout = 10.0,
                         dataLayout = PyDAQmx.DAQmx_Val_GroupByChannel,
                         writeArray = [volt,],
                         reserved = None,
                         sampsPerChanWritten = None
                         )
            

        def write_volt_array(self, volt_array):
            self.task.WriteAnalogF64(
                         numSampsPerChan = len(volt_array),
                         autoStart = False,
                         timeout = 10.0,
                         dataLayout = PyDAQmx.DAQmx_Val_GroupByChannel,
                         writeArray = volt_array,
                         reserved = None,
                         sampsPerChanWritten = ctypes.byref(sampsPerChanWritten)
                         )

