from ScopeFoundry.hardware import HardwareComponent
from ScopeFoundryHW.ni_daq import NI_CounterTask
import time
import numpy as np

class NI_FreqCounterCallBackHW(HardwareComponent):
    
    name = 'ni_freq_counter'
    
    def setup(self):
        
        self.settings.New(  name = 'count_rate', 
                            dtype=float, si=True, ro=True,
                            unit="Hz")
        
        self.settings.New(  name = 'int_time',
                            initial=0.1,
                            dtype=float, si=True,
                            spinbox_decimals = 3,
                            ro=False,
                            unit = "s",
                            vmin = 1e-6, vmax=100)
        
        self.settings.New('live_update', dtype=bool, initial=True)

        self.settings.New('cb_interval', dtype=float, unit='s', si=True,
                          initial=10e-3, vmin=5e-3)
        
        self.settings.New('buffer_size', dtype=int, initial=1000)

        self.settings.New('dev', dtype=str, initial='Dev1')
        
        self.settings.New(  'counter_chan',
                             dtype=str,
                             initial='ctr0',
                             ro=False)

        self.settings.New(  'input_terminal',
                             dtype=str,
                             initial="PFI0",
                             ro=False)
        
    def connect(self):
        S = self.settings
        
        self._ctr_chan = "{}/{}".format(S['dev'], S['counter_chan'])
        self._in_term = "/{}/{}".format(S['dev'], S['input_terminal'])
        
        C = self.counter_task = NI_CounterTask(channel=self._ctr_chan,
                                           input_terminal=self._in_term,
                                           )        
        
        for lq_name in ['int_time', 'cb_interval']:
            self.settings.get_lq(lq_name).connect_to_hardware(
                write_func=self.restart_task
                )
        self.settings.buffer_size.connect_to_hardware(
                write_func=self.create_buffers
                )
        
        self.settings.count_rate.connect_to_hardware(
                read_func = self.read_count_rate
            )
        
        self.create_buffers()
        self.restart_task()
        
        
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'counter_task'):
            self.counter_task.stop()
            del self.counter_task
        
        
    def counter_callback(self):
        """function called every N samples determined by cb_interval setting
        Stores count rate in the buffer
        """
        S = self.settings
        try:
            self.current_count = self.counter_task.read_buffer(count=self.n_samples_cb)[-1]
        except Exception as err:
            self.current_count =0
            self.restart_task()
            raise err
        count_rate = (self.current_count - self.prev_count)/S['cb_interval']
        self.cb_buffer[self.cb_buffer_i] = count_rate
        self.cb_buffer_i += 1
        self.cb_buffer_i %= S['buffer_size']
        self.prev_count = self.current_count
        
        ## averaged over int_time
        if self.mean_count*S['cb_interval'] >= S['int_time'] and (self.mean_count > 0) :
            mean_cr = self.current_mean / self.mean_count
            self.mean_buffer[self.mean_buffer_i] = mean_cr
            if S['live_update']:
                S['count_rate'] = mean_cr
            self.current_mean = 0
            self.mean_count = 0
            self.mean_buffer_i += 1
            self.mean_buffer_i %= S['buffer_size']
        else:
            self.current_mean += count_rate
            self.mean_count +=1
        
        #print("counter_callback")
        
    def restart_task(self, x=None):
        S = self.settings
        C = self.counter_task
        
        SAMPLE_RATE = 100000 # for 100kHz time base
        

        

        self.n_samples_cb = int(SAMPLE_RATE*S['cb_interval'])
        print('restart_task', self.n_samples_cb)
        C.stop()
        C.set_rate(rate=SAMPLE_RATE, finite=False,
               count=self.n_samples_cb*10,
               clk_source="/{}/100kHzTimebase".format(self.settings['dev']))
        C.set_n_sample_callback(n_samples=self.n_samples_cb,
                                cb_func=self.counter_callback)
        self.prev_count = 0
        C.start()
        
    def create_buffers(self, x=None):
        self.cb_buffer = np.zeros(self.settings['buffer_size'], dtype=float) 
        self.cb_buffer_i = 0
        
        self.mean_buffer = np.zeros(self.settings['buffer_size'], dtype=float)
        self.mean_count = 0
        self.mean_buffer_i = 0
        self.current_mean = 0
        
    def wait_and_read_count_rate(self):
        time.sleep(self.settings['int_time'])
        return self.read_count_rate()
    
    def read_count_rate(self):
        return self.mean_buffer[self.mean_buffer_i-1]
