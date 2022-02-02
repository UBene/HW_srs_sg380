from .ni_task_wrap import NI_TaskWrap
from .ni_adc_task import NI_AdcTask
from .ni_dac_task import NI_DacTask
from .ni_counter_task import NI_CounterTask
import PyDAQmx as mx
import numpy as np

import logging

logger = logging.getLogger(__name__)



class NI_SyncTaskSet(object):
    '''
    creates simultaneous input (ADC, counter) and output (DAC) tasks with 
    synchronized start triggers
    input and output task elapsed time need not be equal, but typically will be, 
    can oversample input with for example 10x rate, 10x sample count
    '''
    def __init__(self, out_chan, in_chan,ctr_chans, ctr_terms, vin_range = 10.0, 
                terminalConfig='default', clock_source = "", trigger_output_term=None ):
    
        # create input and output tasks
        self.dac = NI_DacTask( out_chan, name='SyncTaskSet_DAC')        
        self.adc = NI_AdcTask( in_chan, vin_range, 'SyncTaskSet_ADC', terminalConfig )
        self.ctr_chans=ctr_chans
        self.ctr_terms=ctr_terms
        self.num_ctrs=len(self.ctr_chans)
        self.ctrs=[]

        for i in range(self.num_ctrs):
            self.ctrs.append(NI_CounterTask(ctr_chans[i],ctr_terms[i],
                                            name='ctr_{}_{}'.format(ctr_chans[i], ctr_terms[i])))
        
        # if a clock_source is defined, use it to clock the ADC, 
        # otherwise internally clock ADC, rate set during setup()
        self.clock_source = clock_source
        if self.clock_source:
            logger.debug( "setup clock_source" + repr( self.clock_source) )
            self.adc.task.CfgDigEdgeStartTrig(clock_source, mx.DAQmx_Val_Rising)

        # Sync DAC StartTrigger on ADC StartTigger
        buffSize = 512
        buff = mx.create_string_buffer( buffSize )
        self.adc.task.GetNthTaskDevice(1, buff, buffSize)    #DAQmx name for input device
        dac_trig_name = b'/' + buff.value + b'/ai/StartTrigger'
        self.dac.task.CfgDigEdgeStartTrig(dac_trig_name, mx.DAQmx_Val_Rising)


        # Route DAC SampleClock signal to trigger_output_term
        # This allows you to trigger other devices simultaneously with DAC output
        self.trigger_output_term = trigger_output_term
        if self.trigger_output_term:
            self.dac.task.ExportSignal(mx.DAQmx_Val_SampleClock, self.trigger_output_term)
            #self.adc.task.SetDOTristate(trigger_output_term, False)
            
            ## For debugging, send trigger to another pin
            #mx.DAQmxConnectTerms(trigger_output_term, b"/X-6368/PFI12", mx.DAQmx_Val_DoNotInvertPolarity )
            
    def setup(self, rate_out, count_out, rate_in, count_in, is_finite=True):
        """
        Set the i/o rates and size of buffers
        
        *rate_out*: DAC rate (Hz), counters are also clocked at this rate
        *rate_in*: ADC rate (Hz)
        
        *is_finite* defines if single shot or continuous
        
        ADC, Counters lag DAC, 
        ADC reads voltage while DAC is starting to move to voltage
        therefore removing extra values, from ADC, counters may be necessary to align writes/reads
        """
        # Pad removed 2017-02-23 ESB + DFO
        #        *Pad* if true, acquire one extra input value per channel, 
        #        strip off the first read, so writes/reads align
        # if pad:
        #      self.delta = int(np.rint(rate_in / rate_out))
        # else:
        #     self.delta = 0
        
        if rate_in % rate_out > 0:
            logger.warn("NI_SyncTaskSet: rate_in/rate_out is not an integer, funny oversampling will occur")

        self.dac.set_rate(rate_out, count_out, finite=is_finite, clk_source=self.clock_source)
        self.adc.set_rate(rate_in,  count_in  ,finite=is_finite, clk_source=self.clock_source)
        for i in range(self.num_ctrs):
            self.ctrs[i].set_rate(rate_in,count_in,
                                  clk_source='ao/SampleClock',finite=is_finite)
            
        
    def write_output_data_to_buffer(self, data, timeout=0):
        self.dac.load_buffer(data, timeout=timeout)
    
    def start(self):
        for i in range(self.num_ctrs):
            self.ctrs[i].start()
        self.dac.start() #start dac first, waits for trigger from ADC to output data
        self.adc.start()
        
       
    def read_adc_buffer(self, count=0, timeout = 1.0):
        x = self.adc.read_buffer(count=count, timeout=timeout)
        #return x[self.delta*self.adc.get_chan_count()::]
        # Changed 2/10/17: don't remove delta -- works for sync scan,this may break other things!
        return x
    
    def get_adc_chan_count(self):
        return self.adc.get_chan_count()
    
    def read_adc_buffer_reshaped(self, count=0, timeout = 1.0):
        return self.read_adc_buffer(count=count, timeout=timeout).reshape(-1, self.get_adc_chan_count()) 
    
    def read_ctr_buffer(self, ctr_i, count=0, timeout=0):
        """Reads the counter ctr_i buffer up to count,
        if count=0 (default) read up to block_size"""
        x = self.ctrs[ctr_i].read_buffer(count, timeout)
        return x
    
    def read_ctr_buffer_diff(self, ctr_i, count=0, timeout = 0):
        return self.ctrs[ctr_i].read_diff_buffer(count, timeout)
    
    def stop(self):
        logger.debug('dac.task {}'.format( self.dac.task ))
        logger.debug('adc.task {}'.format( self.adc.task ))
        self.dac.stop() 
        self.adc.stop()
        for i in range(self.num_ctrs):
            self.ctrs[i].stop()
        
    def close(self):
        self.dac.close()
        self.adc.close()
        for i in range(self.num_ctrs):
            self.ctrs[i].close()
            
