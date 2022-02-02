from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo import DynamixelServos, control_lut,\
    OperatingModes
import time

class DynamixelXServosHW(HardwareComponent):
    
    name='dynamixel_servos'
    
    def __init__(self, app, debug=False, name=None, devices=dict(servo0=0)):
        
        """
        devices is a dictionary keys: names of servo, values: id values 
        
        """
        self.devices = devices.copy()
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    def setup(self):
        
        self.settings.New('port', dtype=str, initial='COM1')
        
        for sname, sid in self.devices.items():
            
            self.settings.New(sname + "_oper_mode", dtype=str, choices=[x.name for x in OperatingModes])
            
            #self.settings.New(sname + "_model_num", dtype=int)
            for ctrl in control_lut.values():
                self.settings.New(sname + "_" + ctrl.name, dtype=int, ro=(ctrl.access == 'r'))
            
            
            
    def connect(self):
        
        #from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo import DynamixelServos
        
        self.dev = DynamixelServos(port=self.settings['port'])
        
        
        for sname, sid in self.devices.items():
            
            #self.settings[sname + "_model_num"] = self.dev.read_value(sid, 'model_num')

            lq = self.settings.get_lq(sname + "_oper_mode")
            lq.connect_to_hardware(
                read_func = lambda sid=sid: self.dev.read_operating_mode(sid), 
                write_func = lambda mode, sid=sid: self.dev.write_operating_mode(sid, mode)
                )            

            for ctrl in control_lut.values():
                
                lq = self.settings.get_lq(sname + "_" + ctrl.name)
                
                if ctrl.access == 'r':
                    def read_f(sid=sid, ctrl=ctrl):
                        return self.dev.read_value(sid, ctrl.name)
                    lq.connect_to_hardware(read_func=read_f)
                    lq.read_from_hardware()
                elif ctrl.access == 'rw':
                    def read_f(sid=sid, ctrl=ctrl):
                        return self.dev.read_value(sid, ctrl.name)
                    def write_f(new_val, sid=sid,ctrl=ctrl):
                        self.dev.write_value(sid, ctrl.name, new_val)
                    lq.connect_to_hardware(read_func=read_f, write_func=write_f)
                    lq.read_from_hardware()

            
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
    
    
    
    def threaded_update(self):
        import time
        time.sleep(0.100)
        try:
            self.read_from_hardware()
        except Exception as err:
            print(self.name, "Error in treaded_update", err)
            
