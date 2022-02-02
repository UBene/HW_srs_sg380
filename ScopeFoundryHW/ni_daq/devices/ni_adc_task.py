from .ni_task_wrap import NI_TaskWrap
import PyDAQmx as mx
import numpy as np
import logging
logger = logging.getLogger(__name__)


class NI_AdcTask(NI_TaskWrap):
    '''
    Analog to digital input task, inherits from abstract NI_TaskWrap task
    '''
    def __init__(self, channel, range = 10.0, name = '', terminalConfig='default'  ):
        ''' creates ADC task
        Range [+/- 1, 2, 5, 10]
        terminalConfig in ['default', 'rse', 'nrse', 'diff', 'pdiff']
        '''
        assert terminalConfig in  ('default', 'rse', 'nrse', 'diff', 'pdiff')
        
        NI_TaskWrap.__init__(self, name)
        
        self.terminalConfig = terminalConfig
        self._terminalConfig_enum = dict(
              default = mx.DAQmx_Val_Cfg_Default, 
              rse = mx.DAQmx_Val_RSE,
              nrse = mx.DAQmx_Val_NRSE,
              diff = mx.DAQmx_Val_Diff,
              pdiff = mx.DAQmx_Val_PseudoDiff,
              )[self.terminalConfig]

        if self.task:
            self.set_channel(channel, range)
            
        self.done_callback_is_set = False
            
    def set_channel(self, channel, adc_range = 10.0):
        ''' adds input channel[s] to existing task, tries voltage range +/- 1, 2, 5, 10'''
        #  could use GetTaskDevices followed by GetDevAIVoltageRngs to validate max volts
        #  also can check for simultaneous, max single, max multi rates
        self._channel = channel
        self._input_range = min( abs(adc_range), 10.0 ) #error if range exceeds device maximum
        self._sample_count = 0
        adc_max = mx.float64(  self._input_range )
        adc_min = mx.float64( -self._input_range )


        try:                
            #int32 CreateAIVoltageChan( const char physicalChannel[], const char nameToAssignToChannel[], 
            #    int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
            self.task.CreateAIVoltageChan(self._channel, '', self._terminalConfig_enum,
                                          adc_min, adc_max, mx.DAQmx_Val_Volts, '')            
            chan_count = mx.uInt32(0) 
            self.task.GetTaskNumChans(mx.byref(chan_count))
            self._chan_count = chan_count.value
            self._mode = 'single'   #until buffer created
        except mx.DAQError as err:
            self._chan_count = 0
            self.error(err)
            
    def set_rate(self, rate = 1e4, count = 1000, finite = True, clk_source=""):
        """
        Input buffer
            In continuous mode, count determines per-channel buffer size only if
                count EXCEEDS default buffer (1 MS over 1 MHz, 100 kS over 10 kHz, 10 kS over 100 Hz, 1 kS <= 100 Hz
                unless buffer explicitly set by DAQmxCfgInputBuffer()

            In finite mode, buffer size determined by count
         """
        if finite:
            adc_mode = mx.int32(mx.DAQmx_Val_FiniteSamps)
        else:
            adc_mode = mx.int32(mx.DAQmx_Val_ContSamps)
        adc_rate = mx.float64(rate)   #override python type
        adc_count = mx.uInt64(int(count))
        
        self.stop() #make sure task not running, 
        
        #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
        #                        int32 sampleMode, uInt64 sampsPerChan );
        #  default clk_source (clock source) is subsystem acquisition clock (OnboardClock)
        # adc_rate: The sampling rate in samples per second per channel. 
        #             If you use an external source for the Sample Clock, set this value to the maximum expected rate of that clock.  
        try:                 
            self.task.CfgSampClkTiming(clk_source, adc_rate, mx.DAQmx_Val_Rising, adc_mode, adc_count) 
            adc_rate = mx.float64(0)
            #exact rate depends on hardware timer properties, may be slightly different from requested rate
            self.task.GetSampClkRate(mx.byref(adc_rate));
            self._rate = adc_rate.value
            self._count = int(count)
            self._mode = 'buffered'
        except mx.DAQError as err:
            self.error(err)
            self._rate = 0
    
    def set_n_sample_callback(self, n_samples, cb_func):
        """
        Setup callback functions for EveryNSamplesEvent
        *cb_func* will be called with when new data is available
        after every *n_samples* are acquired.
        """
        self.cb_nSamples = n_samples
        self.cb_func = cb_func
        self.task.EveryNCallback = cb_func
        self.task.AutoRegisterEveryNSamplesEvent(
            everyNsamplesEventType=mx.DAQmx_Val_Acquired_Into_Buffer, 
            nSamples=self.cb_nSamples,
            options=0)


        
        
    def set_done_callback(self, done_func):
        'done_func takes one argument (status)'
        self.cb_done_func =  done_func
        self.task.DoneCallback= self.cb_done_func
        if not self.done_callback_is_set:
            self.task.AutoRegisterDoneEvent(options=0)
            self.done_callback_is_set = True

    """def EveryNCallback(self):
        self.data_buffer=self.read_buffer(self.cb_nSamples, timeout=1.0)
        self.cb_func(self.data_buffer)
        return 0 # The function should return an integer
    
    def DoneCallback(self, status):
        self.data_buffer=self.read_buffer(0, timeout=1.0)
        print('done_callback finaldata', self.data_buffer.shape)
        self.cb_func(self.data_buffer)
        self.cb_done_func()
        #print "Status",status.value
        return 0 # The function should return an integer
    """
  
    def set_single(self):
        ''' single-value [multi channel] input, no clock or buffer
                   
            For unbuffered input (one sample per channel no timing or clock),
            if task STARTed BEFORE reading, in tight loop overhead between consecutive reads ~ 36 us with some jitter
                task remains in RUN, must be STOPed or cleared to modify
            if task is COMMITted  before reading, overhead ~ 116 us 
                (implicit transition back to COMMIT instead of staying in RUNNING)
            if task is STOPed before reading, requiring START read STOP overhead 4 ms
         '''
        if self._mode != 'single':
            self.clear()    #delete old task
            self.make_task(self._task_name)
            self.set_channel(self._channel, self._input_range)
            self._mode = 'single'
            
    def get(self):
        ''' reads one sample per channel in immediate (non buffered) mode, fastest if task pre-started'''
        data = np.zeros(self._chan_count, dtype = np.float64 )
        if self._mode != 'single':
            self.set_single()
            self.start()
        read_size = mx.uInt32(self._chan_count)
        read_count = mx.int32(0)
        timeout = mx.float64( 1.0 )
        try:
            # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, 
            #    float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
            self.task.ReadAnalogF64(1, timeout, mx.DAQmx_Val_GroupByScanNumber, 
                                  data, read_size, mx.byref(read_count), None)
        except mx.DAQError as err:
            self.error(err)
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
        assert read_count.value == 1, \
            "sample count {} transfer count {}".format( 1, read_count.value )
        return data
              
    def read_buffer(self, count = 0, timeout = 0):
        ''' reads block of input data, defaults to block size from set_rate()
            for now allocates data buffer, possible performance hit
            in continuous mode, reads all samples available up to block_size
            in finite mode, waits for samples to be available, up to smaller of block_size or
                _chan_cout * _count
                
            for now return interspersed array, latter may reshape into 
        '''
        count = int(count)
        if count == 0:
            count = self._count
        block_size = count * self._chan_count
        data = np.zeros(block_size, dtype = np.float64)
        read_size = mx.uInt32(block_size)
        read_count = mx.int32(0)    #returns samples per chan read
        adc_timeout = mx.float64( timeout )
        try:
            # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, 
            #    float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
            self.task.ReadAnalogF64(-1, adc_timeout, mx.DAQmx_Val_GroupByScanNumber, 
                                  data, read_size, mx.byref(read_count), None)
        except mx.DAQError as err:
            self.error(err)
            #not sure how to handle actual samples read, resize array??
        if read_count.value < count:
            pass
            #logger.warning( 'requested {} values for {} channels, only {} read'.format( count, self._chan_count, read_count.value) )
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
#        assert read_count.value == 1, \
#           "sample count {} transfer count {}".format( 1, read_count.value )
        return data
            