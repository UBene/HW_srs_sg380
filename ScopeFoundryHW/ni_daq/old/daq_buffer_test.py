import numpy as np
import PyDAQmx as mx
from equipment.NI_Daq import NI_TaskWrap
import sched
import time

class BuffTest(NI_TaskWrap):
    
    def __init__(self, channel, range = 10.0, name = '', terminalConfig='default'  ):
        NI_TaskWrap.__init__(self, name)
        ''' creates ADC task
        Range [+/- 1, 2, 5, 10]
        terminalConfig in ['default', 'rse', 'nrse', 'diff', 'pdiff']
        '''
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
            
    def set_rate(self, rate = 1e4, count = 1000, finite = True):
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
        #  default clock source is subsystem acquisition clock
        try:                 
            self.task.CfgSampClkTiming("", adc_rate, mx.DAQmx_Val_Rising, adc_mode, adc_count) 
            adc_rate = mx.float64(0)
            #exact rate depends on hardware timer properties, may be slightly different from requested rate
            self.task.GetSampClkRate(mx.byref(adc_rate));
            self._rate = adc_rate.value
            self._count = count
            self._mode = 'buffered'
        except mx.DAQError as err:
            self.error(err)
            self._rate = 0
            
    def read_buffer(self, count = 0, timeout = 1.0):
        ''' reads block of input data, defaults to block size from set_rate()
            for now allocates data buffer, possible performance hit
            in continuous mode, reads all samples available up to block_size
            in finite mode, waits for samples to be available, up to smaller of block_size or
                _chan_cout * _count
                
            for now return interspersed array, latter may reshape into 
        '''
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
            print 'requested {} values for {} channels, only {} read'.format( count, self._chan_count, read_count.value)
#        print "samples {} written {}".format( self._sample_count, writeCount.value)
#        assert read_count.value == 1, \
#           "sample count {} transfer count {}".format( 1, read_count.value )
        return data
        
if __name__ == '__main__':
    buffer_test=BuffTest('X-6368/ai1')
    buffer_test.set_rate(1e4,1000,False)
    buffer_test.start()
    
    a=buffer_test.read_buffer(1, 10)
    print(a)
      