'''
Created on May 2, 2018

@author: Schuck Lab M1
'''
from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryEquipment.pyhydraharp import HydraHarp400
except Exception as err:
    print("Cannot load required modules for APDCounter using HydraHarp400:", err)
    
import time
import random

class APDCounterHHarpHW(HardwareComponent):

    name = "apd_counter"

    def setup(self):

        # Create logged quantities
        self.apd_count_rate = self.add_logged_quantity(
                                name = 'apd_count_rate', 
                                initial = 0,
                                dtype=float, fmt="%e", ro=True,
                                unit="Hz",
                                vmin=-1, vmax=1e10)
        self.int_time = self.add_logged_quantity(
                                name = 'int_time',
                                initial=0.1, ##Note: when using Hydraharp, need >100ms for each reading
                                dtype=float, fmt="%e", ro=False,
                                unit = "sec",
                                vmin = 1e-6, vmax=100)
        self.int_time.spinbox_decimals = 3


        self.dummy_mode = self.add_logged_quantity(name='dummy_mode', dtype=bool, initial=False, ro=False)
        
        # gui is no longer used
        # connect to gui
        #try:
        #    self.int_time.connect_bidir_to_widget(self.gui.ui.apd_counter_int_doubleSpinBox)
        #except Exception as err:
        #    print("APDCounterHHarpHW: could not connect to custom GUI", err)

    def connect(self):
        if self.debug_mode.val: print("Connecting to APD Counter via HHarp")
        
        # Open connection to hardware

        if not self.dummy_mode.val:
            # Normal APD:  "/Dev1/PFI0"
            # APD on monochromator: "/Dev1/PFI2"
            #self.ni_counter = NI_FreqCounterUSB(debug = self.debug_mode.val, mode='high_freq', input_terminal = "/Dev1/PFI0")
            self.HH_counter = HydraHarp400(devnum=0, mode = 'T2', debug=self.settings['debug_mode'])
            #self.ni_counter = NI_FreqCounterUSB(debug = self.debug_mode.val, mode='large_range', input_terminal = "/Dev1/PFI0")
        else:
            if self.debug_mode.val: print("Connecting to APD Counter vis HHarp (Dummy Mode)")

        # connect logged quantities
        self.apd_count_rate.hardware_read_func = self.read_count_rate

#        try:
#            self.apd_count_rate.updated_text_value.connect(
#                                           self.gui.ui.apd_counter_output_lineEdit.setText)
#        except Exception as err:
#            print("missing gui", err)

    def disconnect(self):
        
        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None

        if hasattr(self, 'HH_counter'):
            #disconnect hardware
            self.HH_counter.close()
    
            # clean up hardware object
            del self.HH_counter
            
            
    def read_count_rate(self):
        if not self.dummy_mode.val:
            dt0 = 0.1 #minimum integration time
            Nt  = self.int_time//dt0
            cr = 0.0
            for idt in range(0, Nt):
                cr += self.HH_counter.read_count_rate0()
                time.sleep(dt0)
            self.c0_rate = cr/Nt
            time.sleep(self.int_time - dt0*Nt)
            return self.c0_rate
        else:
            time.sleep(self.int_time)
            self.c0_rate = random.random()*1e4
            if self.debug_mode.val: print(self.name, "dummy read_count_rate", self.c0_rate)
            return self.c0_rate
