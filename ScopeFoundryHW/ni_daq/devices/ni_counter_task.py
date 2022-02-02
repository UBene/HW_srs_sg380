from .ni_task_wrap import NI_TaskWrap
import PyDAQmx as mx
import numpy as np
import logging
logger = logging.getLogger(__name__)

class NI_CounterTask( NI_TaskWrap ):
    '''
    Event counting input task, inherits from abstract NI_TaskWrap task
    '''
    def __init__(self, channel, input_terminal='PFI0', name = ''  ):
        ''' creates Counter task, default channel names ctr0, ctr1...
            uses input 'PFI0' by default
        '''
        NI_TaskWrap.__init__(self, name)
        

        if self.task:
            self.set_channel(channel, input_terminal)
        else:
            raise IOError("NI_CounterTask failed to create counter task")
            
    def set_channel(self, channel, input_terminal = 'PFI0' ):
        ''' adds input channel[s] to existing task'''
        logger.debug("NI_CounterTask.set_channel-- {} {}".format(channel, input_terminal))
        #  could use GetTaskDevices followed by GetDevAIVoltageRngs to validate max volts
        #  also can check for simultaneous, max single, max multi rates            
        self._channel = channel
        #self._sample_count = 0
        self._input_terminal = input_terminal

        try:                
            #int32 DAQmxCreateCICountEdgesChan (TaskHandle taskHandle, const char counter[], 
            #    const char nameToAssignToChannel[], int32 edge, uInt32 initialCount, int32 countDirection);
            self.task.CreateCICountEdgesChan(self._channel, '', mx.DAQmx_Val_Rising, 0, mx.DAQmx_Val_CountUp )
            self.task.SetCICountEdgesTerm( self._channel, self._input_terminal)
        except mx.DAQError as err:
            #self._chan_count = 0
            self.error(err)
            
    def set_rate(self, rate = 1e4, count = 1000,  clk_source = 'ao/SampleClock', finite = True):
        """
        NOTE analog output and input clocks are ONLY available when NI_DacTask or NI_AdcTask task are running. This
        is OK for simultaneous acquisition. Otherwise use dummy task or use another ctr as a clock. If the 
        analog task completes before the counter task, the sample trigger will no longer arrive
        
        Input buffer
            Uses analog output clock for now, may conflict with DAC tasks
            In continuous mode, count determines per-channel buffer size only if
                count EXCEEDS default buffer (1 MS over 1 MHz, 100 kS over 10 kHz, 10 kS over 100 Hz, 1 kS <= 100 Hz
                unless buffer explicitly set by DAQmxCfgInputBuffer()
    
            In finite mode, buffer size determined by count
        """
        if finite:
            ctr_mode = mx.int32(mx.DAQmx_Val_FiniteSamps)
        else:
            ctr_mode = mx.int32(mx.DAQmx_Val_ContSamps)
        ctr_rate = mx.float64(rate)   #override python type
        ctr_count = mx.uInt64(int(count))
        self._clock_source = clk_source
        
        self.stop() #make sure task not running, 
        #  CfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, 
        #                        int32 sampleMode, uInt64 sampsPerChan );
        #  default clock source is subsystem acquisition clock
        try:                 
            self.task.CfgSampClkTiming(clk_source, ctr_rate, mx.DAQmx_Val_Rising, ctr_mode, ctr_count) 
            #exact rate depends on hardware timer properties, may be slightly different from requested rate
            ctr_rate.value = 0
            self.task.GetSampClkRate(mx.byref(ctr_rate));
            self._rate = ctr_rate.value
            self._count = count
            #self._mode = 'buffered'
        except mx.DAQError as err:
            self.error(err)
            self._rate = 0
    
    def start(self):
        self.prev_count = 0
        NI_TaskWrap.start(self)
        
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


### copied for ADC, probably irrelevant for counter              
#     def set_single(self):
#         ''' single-value [multi channel] input, no clock or buffer
#                    
#             For unbuffered input (one sample per channel no timing or clock),
#             if task STARTed BEFORE reading, in tight loop overhead between consecutive reads ~ 36 us with some jitter
#                 task remains in RUN, must be STOPed or cleared to modify
#             if task is COMMITted  before reading, overhead ~ 116 us 
#                 (implicit transition back to COMMIT instead of staying in RUNNING)
#             if task is STOPed before reading, requiring START read STOP overhead 4 ms
#          '''
#         if self._mode != 'single':
#             self.clear()    #delete old task
#             self.make_task(self._task_name)
#             self.set_channel(self._channel, self._input_terminal)
#             self._mode = 'single'

### copied for ADC, probably irrelevant for counter            
#     def get(self):
#         ''' reads one sample per channel in immediate (non buffered) mode, fastest if task pre-started
#             works rather well for count rates when combined with python time.clock()
#         '''
#         data = np.zeros(1, dtype = np.float64 )
#         data = mx.float64(0)
#         if self._mode != 'single':
#             self.set_single()
#             self.start()
#         read_size = mx.uInt32(self._chan_count)
#         timeout = mx.float64( 1.0 )
#         try:
#             # int32 DAQmxReadCounterScalarF64 (TaskHandle taskHandle, float64 timeout, 
#             #    float64 *value, bool32 *reserved);
#             self.task.ReadCounterScalarF64(timeout, mx.byref(data), None )
# 
#         except mx.DAQError as err:
#             self.error(err)
#         return data.value
    
    def read_buffer(self, count = 0, timeout = 0):
        ''' reads block of input data, defaults to block size from set_rate()
            for now allocates data buffer, possible performance hit
            in continuous mode, reads all samples available up to block_size
            in finite mode, waits for samples to be available, up to smaller of block_size or
                _chan_cout * _count
            
            returns data
        '''
        if count == 0:
            count = self._count
        data = np.zeros(count, dtype = np.float64)
        read_count = mx.int32(0)    #returns samples per chan read
        try:
            # int32 DAQmxReadCounterF64 (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, 
            #    float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
            self.task.ReadCounterF64(-1, timeout, data, count, mx.byref(read_count), None)
        except mx.DAQError as err:
            self.error(err)
            #not sure how to handle actual samples read, resize array??
        if read_count.value < count:
            logger.warn('NI_CounterTask: requested {} values for {} channels, only {} read'.format( count, self._chan_count, read_count.value))
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
#        assert read_count.value == 1, \
#           "sample count {} transfer count {}".format( 1, read_count.value )
        return data[0:read_count.value]
    
    def read_diff_buffer(self, count = 0, timeout = 0):
        data_block = self.read_buffer(count, timeout)
        x=np.insert(data_block,0,self.prev_count)
        x=np.diff(x)
        self.prev_count = data_block[-1]
        return x

