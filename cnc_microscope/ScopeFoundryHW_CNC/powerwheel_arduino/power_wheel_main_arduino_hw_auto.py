'''
Created on Sep 23, 2014

@author: Benedikt 
'''
from ScopeFoundry import HardwareComponent
import time

try:
    from ScopeFoundryHW_CNC.powerwheel_arduino.power_wheel_main_arduino_dev import PowerWheelMainArduino
except Exception as err:
    print("Cannot load required modules for arduino power wheel:", err)



class PowerWheelMainArduinoHW(HardwareComponent): #object-->HardwareComponent
    
    name = 'main_beam_power_wheel'
    debug = False
    
    def setup(self):
        self.debug = True

        # logged quantity        
        self.encoder_pos = self.add_logged_quantity('encoder_pos', dtype=int, unit='steps', ro=True)
        self.move_steps  = self.add_logged_quantity('move_steps',  dtype=int, unit='steps', vmin=1, vmax=3200, initial=10, ro=False)
        self.ser_port = self.add_logged_quantity('ser_port', dtype=str, initial='COM4')
        self.powermeter_type= self.add_logged_quantity("Si", dtype=str, ro=False, 
                                            choices = [("Si","Si"), ("Ge","Ge")]
                                                    )
        #  operations
        self.add_operation("zero_encoder", self.zero_encoder)
        self.add_operation("auto_zero_encoder", self.move_bkwd)
        
        self.add_operation("move_fwd", self.move_fwd)
        self.add_operation("move_bkwd", self.move_bkwd)
        self.app.hardware['thorlabs_powermeter_Si'].power.read_from_hardware(send_signal=True)


    def connect(self):
                
        if self.debug: print("connecting to arduino power wheel")
        
        # Open connection to hardware
        self.power_wheel_dev = PowerWheelMainArduino(port=self.ser_port.val, debug=self.debug_mode.val)
        self.power_wheel_dev.write_speed(40)
        print('speed setting')
        # connect logged quantities
        self.encoder_pos.hardware_set_func = self.power_wheel_dev.write_steps
        self.encoder_pos.hardware_read_func= self.power_wheel_dev.read_encoder

        print('connected to ',self.name)
    

    def disconnect(self):

        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
    
        if hasattr(self, 'power_wheel_1_dev'):
            #disconnect hardware
            self.power_wheel_dev.close()
            
            # clean up hardware object
            del self.power_wheel_dev
        
        print('disconnected ',self.name)
        
    #@QtCore.Slot()
    def move_fwd(self):
        #self.power_wheel_dev.write_steps(self.move_steps.val)
        self.power_wheel_dev.write_steps_and_wait(self.move_steps.val)
        time.sleep(0.2)
        #TODO really should wait until done
        self.power_wheel_dev.read_status()
        self.encoder_pos.read_from_hardware()
        
    #@QtCore.Slot()
    def move_bkwd(self):
        self.power_wheel_dev.write_steps_and_wait(-1 * self.move_steps.val)
        time.sleep(0.2)
        #TODO really should wait until done

        self.encoder_pos.read_from_hardware()
        

    def zero_encoder(self):
        current_pos = self.encoder_pos.value()
        previous_pos = self.encoder_pos.value()
        self.power_wheel_dev.write_zero_encoder()
        self.encoder_pos.read_from_hardware()
        
    def auto_zero_encoder(self):
        if 
            self.powermeter = self.app.hardware.thorlabs_powermeter_Si
        self.power_wheel_dev.write_zero_encoder()
        self.encoder_pos.read_from_hardware()

    def move_relative(self, d_steps):
        self.power_wheel_dev.write_steps_and_wait(d_steps)
        time.sleep(0.2)
        #TODO really should wait until done

        self.encoder_pos.read_from_hardware()
