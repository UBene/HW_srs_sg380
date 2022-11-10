'''
Created on Sep 23, 2014

@author: Benedikt 
'''
from ScopeFoundry import HardwareComponent
import time

try:
    from ScopeFoundryEquipment.thorlabs_ell6k import ThorlabsELL6K
except Exception as err:
    print("Cannot load required modules for dual position slider:", err)



class DualPositionSliderHW(HardwareComponent): #object-->HardwareComponent
    
    name = 'dual_position_slider'
    debug = False
    
    def setup(self):
        self.debug = True

        # logged quantity        
        self.slider_pos = self.add_logged_quantity('slider_pos', dtype=str)
        self.ser_port = self.add_logged_quantity('ser_port', dtype=str, initial='COM11')

        #  operations
        self.add_operation("Close", self.move_fwd)
        self.add_operation("Open", self.move_bkwd)



    def connect(self):
                
        if self.debug: print("connecting to dual position slider")
        
        # Open connection to hardware
        self.dual_positipon_slider_dev = ThorlabsELL6K(port=self.ser_port.val, debug=self.debug_mode.val)
        # connect logged quantities
        self.slider_pos.hardware_read_func = self.dual_positipon_slider_dev.get_position
        
        self.read_from_hardware()
        print('connected to ',self.name)
    

    def disconnect(self):

        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
    
        if hasattr(self, 'dual_positipon_slider_dev'):
            #disconnect hardware
            self.dual_positipon_slider_dev.close()
            
            # clean up hardware object
            del self.dual_positipon_slider_dev
        
        print('disconnected ',self.name)
        

    def move_fwd(self):
        self.dual_positipon_slider_dev.move_forward()
        time.sleep(0.2)

    def move_bkwd(self):
        self.dual_positipon_slider_dev.move_backward()
        time.sleep(0.2)

