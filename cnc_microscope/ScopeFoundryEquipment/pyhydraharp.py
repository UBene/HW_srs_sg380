import ctypes
from ctypes import create_string_buffer, c_int, c_char, c_char_p, c_byte, c_ubyte, c_short, c_double, cdll, pointer, byref, c_uint32
import time
import numpy
import platform
import os
import logging

###Updated for including T2 T3 modes, and using Win64, 05/08/2018, KY



logger = logging.getLogger(__name__)

if platform.architecture()[0] == '64bit':
    #hhlib = ctypes.WinDLL("hhlib64.dll")
    #print ( os.path.join(os.path.dirname(__file__), "hh_dll\hhlib64.dll") ) 
    hhlib = ctypes.WinDLL(os.path.join(os.path.dirname(__file__), "hh_dll\hhlib64.dll"))
    #hhlib = ctypes.WinDLL('C:\Users\Schuck Lab M1\workspace\Microscope1 system\ScopeFoundryEquipment\hh_dll\hhlib64.dll')
   

else:
    hhlib = ctypes.WinDLL(os.path.join(os.path.dirname(__file__), "hh_dll\hhlib.dll"))


#hhlib = ctypes.WinDLL("hhlib.dll")
print (hhlib)

class HydraHarp400(object):

    MODE_HIST = 0
    MODE_T2   = 2
    MODE_T3   = 3
    
    #HISTCHAN  = 65536
    TTREADMAX = 131072  # 128K event records

    def __init__(self, devnum=0, refsource='internal', mode='HIST', debug=False):
        
        self.debug = debug
        
        self.mode = mode
        assert mode in ('HIST', 'T2','T3')
        
        self.devnum = int(devnum)
        
        self._err_buffer = create_string_buffer(40)
        
        
        self.lib_version = create_string_buffer(8)
        self.handle_err( hhlib.HH_GetLibraryVersion(self.lib_version) );
        if self.debug: print ("HHLib Version: '%s'" % self.lib_version.value) #% str(self.lib_version.raw).strip()
        self.lib_version = self.lib_version.value
        
        self.hw_serial = create_string_buffer(8)
        self.handle_err(hhlib.HH_OpenDevice(self.devnum, self.hw_serial))
        if self.debug: print ( "Device %i Found, serial %s" % (self.devnum, self.hw_serial) )
         
        self.refsource = refsource.lower()
        if   self.refsource == 'internal': self.refsource_i = 0
        elif self.refsource == 'external': self.refsource_i = 1
        else: print ("Unknown refsource %s" % self.refsource)
        
        if self.debug:  print ("Initializing the device...")
        
        if self.mode == 'HIST':
            if self.debug: "HIST mode"
            self.handle_err(hhlib.HH_Initialize(self.devnum, self.MODE_HIST, self.refsource_i))
        elif self.mode == 'T2':
            if self.debug: "T2 mode"
            self.handle_err(hhlib.HH_Initialize(self.devnum, self.MODE_T2, self.refsource_i))
        elif self.mode == 'T3':
            if self.debug: "T3 mode"
            self.handle_err(hhlib.HH_Initialize(self.devnum, self.MODE_T3, self.refsource_i))
        time.sleep(0.2) ##Note: need to wait >100ms after HH_Initialize

        hw_model   = create_string_buffer(16)
        hw_partno  = create_string_buffer(8)
        hw_version  = create_string_buffer(8)
        self.handle_err( hhlib.HH_GetHardwareInfo(self.devnum, hw_model, hw_partno ,hw_version) )
        self.hw_model   = hw_model.value
        self.hw_partno  = hw_partno.value
        self.hw_version  = hw_version.value
        print ("Found Model %s Part No %s" % (self.hw_model, self.hw_partno))
        
        self.num_input_channels = c_int()
        self.handle_err( hhlib.HH_GetNumOfInputChannels(self.devnum, byref(self.num_input_channels)) )
        self.num_input_channels = self.num_input_channels.value
        print ("Device has %i input channels" % self.num_input_channels)
        
        #######################################################
        #Out put data arrays
        self.hist_data_channel = [None]*self.num_input_channels
        self.tttr_buffer = numpy.zeros(self.TTREADMAX, dtype=numpy.uint32)
        
        if self.debug: print ("Calibrating...")
        self.handle_err( hhlib.HH_Calibrate(self.devnum) )
        
        # automatically stops acquiring a histogram when a bin is filled to 2**16
        self.handle_err(hhlib.HH_SetStopOverflow(self.devnum,1,65535)) 
        
        
        self.CFDLevel = numpy.array([100, 100])
        self.CFDZeroCross = numpy.array([10, 10])

    def handle_err(self, retcode):
        if retcode < 0:
            hhlib.HH_GetErrorString(self._err_buffer, retcode)
            self.err_message = self._err_buffer.value
            raise IOError(self.err_message)
        return retcode
    
    def setup_experiment(self,
            Binning = 0,
            #Range=0, 
            Offset=0, ##Note this offset is in Nanosecond!!
            Tacq=1000, #Measurement time in millisec, you can change this
            SyncDivider = 8, ###Typically need 8 for 80MHz Ti:Saph. The actuall divided freq cannot be higher than 12.5mHz
            SyncChannelOffset = 0, #in ps
            InputChannelOffset = 0,
            SyncCFDZeroCross = 10, SyncCFDLevel = 70, 
            InputCFDZeroCross0 = 10, InputCFDLevel0 = 70,
            InputCFDZeroCross1 = 10, InputCFDLevel1 = 70):
        
        
        #self.Binning = int(Binning)
        #self.handle_err( hhlib.HH_SetBinning(self.devnum, self.Binning) )
        
        
        
        #Resolution = c_double()
        #self.handle_err( hhlib.HH_GetResolution(self.devnum, byref(Resolution)) )
        #self.Resolution = Resolution.value
        
        if self.mode == 'HIST':
            MAXLENCODE = 6 ###can use 0 to 6
            HistLen = c_int()
            self.handle_err( hhlib.HH_SetHistoLen(self.devnum, MAXLENCODE, byref(HistLen)) )
            self.HistLen = HistLen.value
        
        self.write_Binning(Binning)
        
        #self.Tacq = int(Tacq)
        
        self.Tacq = self.set_Tacq(Tacq)

        #self.SyncDivider = int(SyncDivider)
        #self.handle_err( hhlib.HH_SetSyncDiv(self.devnum, self.SyncDivider) )
        
        self.write_SyncDivider(SyncDivider)
        
        #self.Offset = int(Offset)
        #self.handle_err( hhlib.HH_SetOffset(self.devnum, self.Offset) )
        
        self.write_SyncOffset(Offset)
        
        #self.SyncChannelOffset = int(SyncChannelOffset)
        #self.handle_err( hhlib.HH_SetSyncChannelOffset(self.devnum, self.SyncChannelOffset) )
        
        self.write_SyncChannelOffset(SyncChannelOffset)
        
        #self.SyncCFDLevel = int(SyncCFDLevel)
        #self.SyncCFDZeroCross = int(SyncCFDZeroCross)
        #self.handle_err( hhlib.HH_SetSyncCFD(self.devnum, self.SyncCFDLevel, self.SyncCFDZeroCross) )

        #print('*****Writing CFDs*****, SyncCFDLevel = {}'.format(SyncCFDLevel))
        self.write_SyncCFD(SyncCFDLevel, SyncCFDZeroCross)

        #self.InputCFDLevel = int(InputCFDLevel)
        #self.InputCFDZeroCross = int(InputCFDZeroCross) 
        #for chan_num in range(self.num_input_channels):
            #self.handle_err( hhlib.HH_SetInputCFD(self.devnum, chan_num, self.InputCFDLevel, self.InputCFDZeroCross) )
            #self.handle_err( hhlib.HH_SetInputChannelOffset(self.devnum, chan_num, 0) )
        
        self.write_InputCFD(0, InputCFDLevel0, InputCFDZeroCross0)
        self.write_InputCFD(1, InputCFDLevel1, InputCFDZeroCross1)
        

        
        #Note: after Init or SetSyncDiv you must allow >400 ms for valid new count rate readings
        time.sleep(0.4)
        
        self.read_count_rates()
        self.read_Resolution()
            
        # TODO HH_GetWarnings

        if self.debug: print ("Resolution=%1dps Countrate0=%1d/s Countrate1=%1d/s" % (self.Resolution, self.Countrate0, self.Countrate1))
        #if self.debug: print ("Countrate0=%1d/s Countrate1=%1d/s" % ( self.Countrate[0], self.Countrate[1]))

        #self.handle_err( hhlib.HH_SetStopOverflow(self.devnum,0,65535) )
    
    
    def set_Tacq(self, Tacq):
        "Set Acquisition time in milliseconds"
        self.Tacq = int(Tacq)
        return self.Tacq
    
    def set_Tacq_seconds(self, t_sec):
        "Set Acquisition time in seconds"
        return self.set_Tacq(t_sec*1000) / 1000.
    
    def get_Tacq_seconds(self):
        return self.Tacq * 1.0e-3

    def write_SyncDivider(self, SyncDivider):
        self.SyncDivider = int(SyncDivider)
        if self.debug: logger.debug( "write_SyncDivider " + str(self.SyncDivider) )
        self.handle_err(hhlib.HH_SetSyncDiv(self.devnum, self.SyncDivider))
        #Note: after Init or SetSyncDiv you must allow 100 ms for valid new count rate readings
        time.sleep(0.11)
    
    def write_SyncCFD(self, synclevel, synczerocross):
        self.SyncCFDLevel = int(synclevel)
        self.SyncCFDZeroCross = int(synczerocross)
        if self.debug: logger.debug( "write_SyncCFD {} {}".format( synclevel, synczerocross))
        self.handle_err(hhlib.HH_SetSyncCFD(self.devnum, int(synclevel), int(synczerocross)))
    
    def write_InputCFD(self, chan, level, zerocross):
        
        #print('debug check: ', self.CFDLevel)
        
        self.CFDLevel[chan] = int(level)
        self.CFDZeroCross[chan] = int(zerocross)
        if self.debug: logger.debug( "write_InputCFD {} {} {}".format( chan, level, zerocross))
        self.handle_err(hhlib.HH_SetInputCFD(self.devnum, chan, int(level), int(zerocross)))
        
    def write_CFDLevel0(self, level):
        self.write_InputCFD(0, level, self.CFDZeroCross[0])
        
    def write_CFDLevel1(self, level):
        self.write_InputCFD(1, level, self.CFDZeroCross[1])

    def write_CFDZeroCross0(self, zerocross):
        self.write_InputCFD(0, self.CFDLevel[0], zerocross)
    
    def write_CFDZeroCross1(self, zerocross):
        self.write_InputCFD(1, self.CFDLevel[1], zerocross)
        
    def write_Binning(self, Binning):
        self.Binning = int(Binning)
        #############################################
        self.read_max_bin()
        if Binning >= self.MaxBinStep:
            print ('Error: HydraHarp binning step is larger than allowed by MaxBinStep, set to MaxBinStep-1')
            self.Binning = int(self.MaxBinStep-1)
        ##############################################################
        
        self.handle_err(hhlib.HH_SetBinning(self.devnum, self.Binning))
        self.read_Resolution()
        self.time_array = numpy.arange(self.HistLen, dtype=float)*self.Resolution
    
    def read_max_bin(self):
        base_r = c_double(0)
        max_b = c_int(0)
        self.handle_err( hhlib.HH_GetBaseResolution(self.devnum, byref(base_r), byref(max_b)) )
        self.MaxBinStep = max_b.value
        print("max_bin:", self.MaxBinStep)
        return self.MaxBinStep
        
        
    def read_Resolution(self):
        r = c_double(0)
        self.handle_err(hhlib.HH_GetResolution(self.devnum, byref(r)))
        self.Resolution = r.value
        return self.Resolution

    def write_SyncOffset(self, SyncOffset):
        """
        :param SyncOffset: time offset in NANOSECONDS
        :type SyncOffset: int
        """     
        self.SyncOffset = int(SyncOffset)
        self.handle_err(hhlib.HH_SetOffset(self.devnum, self.SyncOffset))
        
    def write_SyncChannelOffset(self, SyncChannelOffset):
        """
        :param SyncChannelOffset: time offset in picoseconds
        :type SyncChannelOffset: int
        """     
        self.SyncChannelOffset = int(SyncChannelOffset)
        self.handle_err(hhlib.HH_SetSyncChannelOffset(self.devnum, self.SyncChannelOffset))


    def read_count_rate(self, chan):        #Note: need to wait 100ms for each reading
        cr = c_int(-1)
        self.handle_err(hhlib.HH_GetCountRate(self.devnum, chan, byref(cr)))
        if chan == 0:
            self.Countrate0 = cr.value
            
        if chan == 1:
            self.Countrate1 = cr.value
        return cr.value
    
    def read_count_rate0(self):
        self.Countrate0 = self.read_count_rate(0)
        return self.Countrate0
    
    def read_count_rate1(self):
        self.Countrate1 = self.read_count_rate(1)
        return self.Countrate1

    def read_count_rates(self):
        self.read_count_rate0()
        self.read_count_rate1()
        return self.Countrate0, self.Countrate1
        
        
    #def read_count_rates(self):     #
    #    sr = c_int()
    #    cr = c_int()
    #    self.handle_err( hhlib.HH_GetSyncRate(self.devnum, byref(sr)) )
    #    self.Syncrate = sr.value
    #    self.Countrate = numpy.zeros(self.num_input_channels, dtype=int)
    #    for chan_num in range(self.num_input_channels):
    #        self.handle_err( hhlib.HH_GetCountRate(self.devnum, chan_num, byref(cr)) )
    #        self.Countrate[chan_num] = cr.value
    #       
    #   return self.Syncrate, self.Countrate
        
    def start_histogram(self, Tacq=None):
        if self.debug: print ("Starting Histogram")
        self.handle_err( hhlib.HH_ClearHistMem(self.devnum) )
        
        self.start_measure(Tacq)
        
    def start_measure(self, Tacq=None):
        if self.debug: print ("HH Starting Measurement")
    
        # set a new acquisition time if given
        if Tacq:
            self.Tacq = int(Tacq)
            
        self.handle_err( hhlib.HH_StartMeas(self.devnum, self.Tacq) )    
        
        return
    
    def check_done_scanning(self):
        status = c_int()
        self.handle_err( hhlib.HH_CTCStatus(self.devnum, byref(status)) )
        if status.value == 0: # not done
            return False
        else: # scanning done
            return True
            
    def stop_histogram(self):
        if self.debug: print ("Stop Histogram")
        return self.stop_measure()
        
    def stop_measure(self):
        if self.debug: print ("Stop Measure")
        self.handle_err( hhlib.HH_StopMeas(self.devnum) )

        
    def read_histogram_data(self, channel=0, clear_after=True):
        channel = int(channel)
        if self.debug: print ("Read Histogram Data for channel %i" % channel)
        
        #unsigned int counts[HISTCHAN];
        #self.hist_data = numpy.zeros(self.HISTCHAN, dtype=numpy.uint32)
        #retcode = hhlib.HH_GetBlock(self.devnum, self.hist_data.ctypes.data, 0) # grab block 0
        
        self.hist_data_channel[channel] = numpy.zeros(self.HistLen, dtype=numpy.uint32)
        self.handle_err(hhlib.HH_GetHistogram(self.devnum, 
                                        self.hist_data_channel[channel].ctypes.data_as(ctypes.POINTER(c_uint32)), 
                                        channel,
                                        int(clear_after)))

        return self.hist_data_channel[channel]
    
    def read_fifo(self, max_count=TTREADMAX):
        nactual = c_int()
        #blocksz = TTREADMAX; // in steps of 512
        assert max_count % 512 == 0
        self.handle_err(hhlib.HH_ReadFiFo(self.devnum, 
                                          self.tttr_buffer.ctypes.data_as(ctypes.POINTER(c_uint32)), 
                                          max_count, 
                                          byref(nactual)))
        
        return nactual.value, self.tttr_buffer
    
    def write_stop_overflow(self, stop_on_overflow=True, stopcount=65535):
        """
        This setting determines if a measurement run will stop if any channel 
        reaches the maximum set by stopcount. If stop_ofl is 0
        the measurement will continue but counts above 65,535 in any bin will be clipped.
        """
        
        if stop_on_overflow:
            overflow_int = 1
        else:
            overflow_int = 0
        
        self.handle_err(hhlib.HH_SetStopOverflow(self.devnum, overflow_int, stopcount))
    
    def close(self):
        return self.handle_err(hhlib.HH_CloseDevice(self.devnum) )
                               
                               
#if __name__ == '__main__':
#    import pylab as pl
#    hh = HydraHarp400(debug = True, mode = 'HIST')
#    hh.read_max_bin()
#    print(hh.MaxBinStep)
#    hh.close()
    
     
#     ## APD reader test
#     hh = HydraHarp400(debug = True, mode = 'T2')
#     print ( hh.read_count_rates() )
#     
#     cr_data = numpy.array([])
#     for i in range(0, 100):
#         cr_data = numpy.hstack( (cr_data, hh.read_count_rate0()) )
#         time.sleep(0.1)
#     
#     hh.close()
#     
#     pl.figure(1)
#     pl.plot(cr_data)
#     pl.show()
#     
    
    
    
    
    ###T2 mode test
#     hh = HydraHarp400(debug=True, mode='T2')
#     print ( hh.read_count_rates() )
#     hh.setup_experiment()#Bining, Range, Offset, Tacq, SyncDivider, SyncCFDZeroCross, SyncCFDLevel, InputCFDZeroCross, InputCFDLevel)
#     hh.start_measure(Tacq=3000)
#     t0 = time.time()
#     while not hh.check_done_scanning():
#         print ("acquiring: ", time.time() - t0, " sec")
#         nactual, buffer = hh.read_fifo()
#         time.sleep(0.3)
#         
#     hh.stop_measure()
#     print ( 'T2 measurement done' )
#     print(numpy.size(buffer))
#     print ('nactual: ', nactual)
#     print('number of nonzero events in fifo: ', numpy.size(buffer[buffer!=0])) #???
#     
#     ####conver to binary array
#     numpy.savetxt('T2_fifo.txt', buffer)
#     
#     buffer_bin_file = open("T2_fifo_bin.txt", "w")
#     buffer_bin = []
#     for bf in buffer:
#         buffer_bin.append( bin(bf)[2:].zfill(32) )
#         buffer_bin_file.write( bin(bf)[2:].zfill(32) )
#         buffer_bin_file.write( '\n' )
#     buffer_bin_file.close()
    

        


    
    
    
#     ###Hist mode test
#     hh = HydraHarp400(debug=True, mode='HIST')
#     print ( hh.read_count_rates() )
#     hh.setup_experiment()#Bining, Range, Offset, Tacq, SyncDivider, SyncCFDZeroCross, SyncCFDLevel, InputCFDZeroCross, InputCFDLevel)
#     hh.start_histogram(Tacq=2300)
#     t0 = time.time()
#     while not hh.check_done_scanning():
#         print ("acquiring: ", time.time() - t0, " sec")
#         time.sleep(0.1)
#     hh.stop_histogram()
#     hh.read_histogram_data(channel=0)
#     print ( hh.read_count_rates() )
#     
#     pl.figure(1)
#     pl.plot(hh.hist_data_channel[0])
#     pl.show()