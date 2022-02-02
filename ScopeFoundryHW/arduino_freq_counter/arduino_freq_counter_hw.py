from ScopeFoundry import HardwareComponent
import threading

class ArduinoFreqCounter(HardwareComponent):
    
    name = 'arduino_freq_counter'
    
    def setup(self):
        
        self.settings.New('port', dtype=str, intital='COM10')
        
        self.settings.New('int_time',
                                initial=0.1,
                                dtype=float, si=True, ro=False,
                                unit = "sec",
                                vmin = 0.005, vmax=10)
        self.settings.New('count_rate', dtype=float, ro=True, unit='Hz', si=True)
        
    def connect(self):
        import serial
        
        self.lock = threading.Lock()
        
        self.ser = serial.Serial(self.settings['port'], baud_rate=57600, timeout=10)
        
        # connect int 
        
        self.settings.int_time.write_to_hardware()
        
        # connect count_rate
        
        
        # threaded update
        
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'ser'):
            self.ser.close()
            del self.ser
            
    def write_int_time(self, new_int_time):
        #convert to ms
        val = int(new_int_time*1000)
        
        with self.lock:
            self.ser.write("g{:d}\n".format(val).encode())
            

    def read_count_rate(self):
        with self.lock:
            #clear first?
            self.ser.reset_input_buffer()
            resp = self.ser.readline()
        return float(resp)
            
            
    def on_threaded_update(self):
        pass
    