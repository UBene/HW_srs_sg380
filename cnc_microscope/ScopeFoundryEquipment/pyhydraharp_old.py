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
    #phlib = ctypes.WinDLL("phlib64.dll")
    print ( os.path.join(os.path.dirname(__file__), "hh_dll\hhlib64.dll") )
    hhlib = ctypes.WinDLL(os.path.join(os.path.dirname(__file__), "hh_dll\hhlib64.dll"))

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
            if self.debug: "T2 mode"
            self.handle_err(hhlib.HH_Initialize(self.devnum, self.MODE_T3, self.refsource_i))

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
        self.handle_err(phlib.HH_SetStopOverflow(self.devnum,1,65535)) 

    def handle_err(self, retcode):
        if retcode < 0:
            hhlib.HH_GetErrorString(self._err_buffer, retcode)
            self.err_message = self._err_buffer.value
            raise IOError(self.err_message)
        return retcode
    
    def setup_experiment(self,
            Binning = 0,
            #Range=0, 
            Offset=0, 
            Tacq=1000, #Measurement time in millisec, you can change this
            SyncDivider = 8,
            SyncChannelOffset = 0,
            SyncCFDZeroCross = 10, SyncCFDLevel = 100, 
            InputCFDZeroCross = 10, InputCFDLevel = 100):

        self.Tacq = int(Tacq)

        self.SyncDivider = int(SyncDivider)
        self.handle_err( hhlib.HH_SetSyncDiv(self.devnum, self.SyncDivider) )
        
        self.SyncCFDLevel = int(SyncCFDLevel)
        self.SyncCFDZeroCross = int(SyncCFDZeroCross)
        self.handle_err( hhlib.HH_SetSyncCFD(self.devnum, self.SyncCFDLevel, self.SyncCFDZeroCross) )

        self.SyncChannelOffset = int(SyncChannelOffset)
        self.handle_err( hhlib.HH_SetSyncChannelOffset(self.devnum, self.SyncChannelOffset) )

        self.InputCFDLevel = int(InputCFDLevel)
        self.InputCFDZeroCross = int(InputCFDZeroCross) 
        for chan_num in range(self.num_input_channels):
            self.handle_err( hhlib.HH_SetInputCFD(self.devnum, chan_num, self.InputCFDLevel, self.InputCFDZeroCross) )
            self.handle_err( hhlib.HH_SetInputChannelOffset(self.devnum, chan_num, 0) )

        if self.mode == 'HIST':
            MAXLENCODE = 6 ###can use 0 to 6
            HistLen = c_int()
            self.handle_err( hhlib.HH_SetHistoLen(self.devnum, MAXLENCODE, byref(HistLen)) )
            self.HistLen = HistLen.value
        
        self.Binning = int(Binning)
        self.handle_err( hhlib.HH_SetBinning(self.devnum, self.Binning) )
        
        self.Offset = int(Offset)
        self.handle_err( hhlib.HH_SetOffset(self.devnum, self.Offset) )
        
        Resolution = c_double()
        self.handle_err( hhlib.HH_GetResolution(self.devnum, byref(Resolution)) )
        self.Resolution = Resolution.value
        
        #Note: after Init or SetSyncDiv you must allow >400 ms for valid new count rate readings
        time.sleep(0.4)
        
        self.read_count_rates()
            
        # TODO HH_GetWarnings

        if self.debug: print ("Resolution=%1dps Countrate0=%1d/s Countrate1=%1d/s" % (self.Resolution, self.Countrate[0], self.Countrate[1]))
        #if self.debug: print ("Countrate0=%1d/s Countrate1=%1d/s" % ( self.Countrate[0], self.Countrate[1]))

        self.handle_err( hhlib.HH_SetStopOverflow(self.devnum,0,65535) )
        
        
    def read_count_rates(self):     #
        sr = c_int()
        cr = c_int()
        self.handle_err( hhlib.HH_GetSyncRate(self.devnum, byref(sr)) )
        self.Syncrate = sr.value
        self.Countrate = numpy.zeros(self.num_input_channels, dtype=int)
        for chan_num in range(self.num_input_channels):
            self.handle_err( hhlib.HH_GetCountRate(self.devnum, chan_num, byref(cr)) )
            self.Countrate[chan_num] = cr.value
            
        return self.Syncrate, self.Countrate
        
    def start_histogram(self, Tacq=None):
        if self.debug: print ("Starting Histogram")
        self.handle_err( hhlib.HH_ClearHistMem(self.devnum) )
        
        self.start_measure(Tacq)
        
    def start_measure(self, Tacq=None):
        if self.debug: print ("Starting Measurement")
    
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
        self.stop_measure()
        
    def stop_measure(self):
        if self.debug: print ("Stop Measure")
        self.handle_err( hhlib.HH_StopMeas(self.devnum) )

        
    def read_histogram_data(self, channel=0, clear_after=True):
        channel = int(channel)
        if self.debug: print ("Read Histogram Data for channel %i" % channel)
        
        #unsigned int counts[HISTCHAN];
        #self.hist_data = numpy.zeros(self.HISTCHAN, dtype=numpy.uint32)
        #retcode = phlib.PH_GetBlock(self.devnum, self.hist_data.ctypes.data, 0) # grab block 0
        
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


if __name__ == '__main__':
    
    import pylab as pl
    
    ###T2 mode test
    hh = HydraHarp400(debug=True, mode='T2')
    print ( hh.read_count_rates() )
    hh.setup_experiment()#Bining, Range, Offset, Tacq, SyncDivider, SyncCFDZeroCross, SyncCFDLevel, InputCFDZeroCross, InputCFDLevel)
    hh.start_measure(Tacq=3000)
    t0 = time.time()
    while not hh.check_done_scanning():
        print ("acquiring: ", time.time() - t0, " sec")
        nactual, buffer = hh.read_fifo()
        time.sleep(0.3)
        
    hh.stop_measure()
    print ( 'T2 measurement done' )
    print(numpy.size(buffer))
    print ('nactual: ', nactual)
    print('number of nonzero events in fifo: ', numpy.size(buffer[buffer!=0])) #???
    
    ####conver to binary array
    numpy.savetxt('T2_fifo.txt', buffer)
    
    buffer_bin_file = open("T2_fifo_bin.txt", "w")
    buffer_bin = []
    for bf in buffer:
        buffer_bin.append( bin(bf)[2:].zfill(32) )
        buffer_bin_file.write( bin(bf)[2:].zfill(32) )
        buffer_bin_file.write( '\n' )
    buffer_bin_file.close()
    

        


    
    
    
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