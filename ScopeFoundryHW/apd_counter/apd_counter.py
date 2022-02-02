from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryHW.ni_daq import NI_FreqCounter
except Exception as err:
    print("Cannot load required modules for APDCounter:", err)
    
import time
import random

class APDCounterHW(HardwareComponent):

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
                                initial=0.1,
                                dtype=float, fmt="%e", ro=False,
                                unit = "sec",
                                vmin = 1e-6, vmax=100)
        self.int_time.spinbox_decimals = 3
        self.counter_mode = self.add_logged_quantity('counter_mode',
                                                     dtype=str,
                                                     initial='large_range',
                                                     ro=False,
                                                     choices=[('Large Range', 'large_range'),
                                                              ('High Freq', 'high_freq'),
                                                              ('Low Freq', 'low_freq')]
                                                     )
        self.counter_chan = self.add_logged_quantity('counter_chan',
                                                     dtype=str,
                                                     initial='Dev1/ctr1',
                                                     ro=False)

        self.input_terminal = self.add_logged_quantity('input_terminal',
                                                     dtype=str,
                                                     initial="/Dev1/PFI0",
                                                     ro=False)
        
        self.dummy_mode = self.add_logged_quantity(name='dummy_mode', dtype=bool, initial=False, ro=False)
        

    def connect(self):
        if self.debug_mode.val: print("Connecting to APD Counter", self.input_terminal.val)
        
        # Open connection to hardware
        self.input_terminal.change_readonly(True)

        if not self.dummy_mode.val:
            # Normal APD:  "/Dev1/PFI0"
            # APD on monochromator: "/Dev1/PFI2"
            self.ni_counter = NI_FreqCounter(
                                             debug = self.debug_mode.val, 
                                             mode=self.counter_mode.val, 
                                             counter_chan=self.counter_chan.val, 
                                             input_terminal = self.input_terminal.val)
            self.ni_counter.start()
        else:
            if self.debug_mode.val: print("Connecting to APD Counter (Dummy Mode)")

        # connect logged quantities
        self.apd_count_rate.hardware_read_func = self.read_count_rate

        try:
            self.apd_count_rate.updated_text_value.connect(
                                           self.gui.ui.apd_counter_output_lineEdit.setText)
        except Exception as err:
            print("missing gui", err)

    def disconnect(self):
        
        #disconnect logged quantities from hardware
        for lq in self.settings.as_dict().values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
            
        if hasattr(self, 'ni_counter'):
            #disconnect hardware
            self.ni_counter.stop()
            self.ni_counter.close()
                        
            # clean up hardware object
            del self.ni_counter
        
    def read_count_rate(self):
        if not self.dummy_mode.val:
            try:
                #self.ni_counter.start()
                self.c0_rate = self.ni_counter.read_average_freq_in_buffer()
                time.sleep(self.int_time.val)
                self.c0_rate = self.ni_counter.read_average_freq_in_buffer()
            except Exception as E:
                raise(E)
                self.c0_rate = -1
                self.log.warm( E )
                #self.ni_counter.reset()
            finally:
                pass # self.ni_counter.stop()
            return self.c0_rate

        else:
            time.sleep(self.int_time.val)
            self.c0_rate = random.random()*1e4
            if self.debug_mode.val: print(self.name, "dummy read_count_rate", self.c0_rate)
            return self.c0_rate
