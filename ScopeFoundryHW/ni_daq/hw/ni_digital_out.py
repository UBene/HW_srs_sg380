from ScopeFoundry import HardwareComponent
import PyDAQmx as mx
import numpy as np

class NIDigitalOutHW(HardwareComponent):
    
    name = 'ni_digital_out'
    
    def __init__(self, app, debug=False, name=None, line_names="01234567"):
        self.line_names = line_names
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):
        
        self.settings.New("port", dtype=str, initial="Dev1/port0/line0:7")
        
        self.line_pins = dict()
        
        for pin_i, line_name in enumerate(self.line_names):
            if line_name == '_':
                continue
            
            self.line_pins[line_name] = pin_i
                        
            self.settings.New(name=line_name, dtype=bool)

            
            
            
            
    def connect(self):
        
        
        self.task = mx.Task()
        self.task.CreateDOChan(self.settings['port'], "", mx.DAQmx_Val_ChanForAllLines)
        
        for line_name, pin in self.line_pins.items():
            self.settings.get_lq(line_name).connect_to_hardware(
                write_func=self.write_digital_lines
                )

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'task'):
            self.task.StopTask()
            del self.task
        
    def write_digital_lines(self, x=None):
        writeArray = np.zeros(8, dtype=mx.c_uint8)
        
        for line_name, pin in self.line_pins.items():
            pin_bool = int(self.settings[line_name])
            #writeArray[0]  = writeArray[0] | pin_bool<<pin
            writeArray[pin] = pin_bool
        
        # DAQmxWriteDigitalLines (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, uInt8 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
        sampsPerChanWritten = mx.c_int32()
        self.task.WriteDigitalLines(numSampsPerChan=1, autoStart=True, timeout=0, 
                                    dataLayout=mx.DAQmx_Val_GroupByChannel, 
                                    writeArray=writeArray, sampsPerChanWritten=mx.byref(sampsPerChanWritten), reserved=None)
        
        print("write_digital_lines writeArray", writeArray)
        print("write_digital_lines sampsPerChanWritten", sampsPerChanWritten.value)


        
        