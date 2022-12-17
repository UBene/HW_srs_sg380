from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryEquipment.ni_freq_counter import NI_FreqCounter
except Exception as err:
    print ("Cannot load required modules for APDCounter:", err)
    
import time
import random

class APDCounterHW(HardwareComponent):

    #name = "apd_counter"

    def setup(self):
        
        self.name = 'apd_counter'

        # Create logged quantities
        
        self.input_terminal = self.add_logged_quantity(
                                name='input_terminal',
                                initial='/Dev1/PFI0',
                                dtype=str,
                                ro=False)
        
        self.apd_count_rate = self.add_logged_quantity(
                                name = 'apd_count_rate', 
                                initial = 0,
                                dtype=float, fmt="%e", ro=True,
                                unit="Hz",
                                vmin=-1, vmax=1e10)
        self.int_time = self.add_logged_quantity(
                                name = 'int_time',
                                initial=0.1,
                                dtype=float, fmt="%e", ro=False,
                                unit = "sec",
                                vmin = 1e-6, vmax=100)
        self.int_time.spinbox_decimals = 3


        self.dummy_mode = self.add_logged_quantity(name='dummy_mode', dtype=bool, initial=False, ro=False)
        
        # connect to gui
        #try:
        #    self.int_time.connect_bidir_to_widget(self.gui.ui.apd_counter_int_doubleSpinBox)
        #except Exception as err:
        #    print ("APDCounterHardwareComponent: could not connect to custom GUI", err)

    def connect(self):
        if self.debug_mode.val: print ("Connecting to APD Counter ", self.input_terminal.val)
        
        # Open connection to hardware
        self.input_terminal.change_readonly(True)

        if not self.dummy_mode.val:
            # Normal APD:  "/Dev1/PFI0"
            # APD on monochromator: "/Dev1/PFI2"
            self.ni_counter = NI_FreqCounter(debug = self.debug_mode.val, mode='high_freq', input_terminal = self.input_terminal.val)
                                             #input_terminal = "/Dev1/PFI0")
        else:
            if self.debug_mode.val: print ("Connecting to APD Counter (Dummy Mode)")

        # connect logged quantities
        self.apd_count_rate.hardware_read_func = self.read_count_rate
        
        self.read_from_hardware()
        
        #self.int_time.hardware_read_func = self.

        #try:
        #    self.apd_count_rate.updated_text_value.connect(
        #                                   self.gui.ui.apd_counter_output_lineEdit.setText)
        #except Exception as err:
        #    print ("missing gui", err)

    def disconnect(self):
        self.input_terminal.change_readonly(False)

        #disconnect hardware
        if hasattr(self, 'ni_counter'):
            self.ni_counter.close()
            
            # clean up hardware object
            del self.ni_counter
        
        #disconnect logged quantities from hardware
        #for lq in self.logged_quantities.values():
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        
        
    def read_count_rate(self):
        if not self.dummy_mode.val:
            try:
                self.ni_counter.start()
                time.sleep(self.int_time.val)
                self.c0_rate = self.ni_counter.read_average_freq_in_buffer()
            except Exception as E:
                print (E)
                #self.ni_counter.reset()
            finally:
                self.ni_counter.stop()
            return self.c0_rate

        else:
            time.sleep(self.int_time.val)
            self.c0_rate = random.random()*1e4
            if self.debug_mode.val: print (self.name, "dummy read_count_rate", self.c0_rate)
            return self.c0_rate
