from threading import Lock
import ctypes
from ctypes import create_string_buffer, c_int, byref, c_uint32, c_double
import numpy

STOPCNTMIN = 1
STOPCNTMAX = 4294967295 # //32 bit is mem max
MAXLENCODE = 6 # max length code histo mode
SYNCDIVMIN = 1
SYNCDIVMAX = 16


class HydraHarp400(object):

    def __init__(self, devnum=0, mode='HIST', refsource='internal', debug=False):
        
        self.debug = debug
        # TODO connect by serial number
        
        self.devnum = devnum
        self.mode = mode.upper()
        self.refsource=refsource.lower()
        
        self.lock = Lock()
        
        self.hhlib = ctypes.WinDLL("hhlib64.dll")

        try:

            # HH_GetLibraryVersion
            lib_version = create_string_buffer(8)
            self._err(self.hhlib.HH_GetLibraryVersion(lib_version))
            self.lib_version = lib_version.value
            if self.debug: print("HHLib Version: '%s'" % self.lib_version)
            
            # HH_OpenDevice
            hw_serial = create_string_buffer(8)
            with self.lock:
                self._err(self.hhlib.HH_OpenDevice(self.devnum, hw_serial)) 
            self.hw_serial = hw_serial.value
            
        
            # HH_Initialize
            mode_id_dict = {"HIST":0, "T2":2, "T3":3, "CONT": 8}
            refsrc_id_dict = {'internal':0, 'external':1}
            with self.lock:
                self._err(self.hhlib.HH_Initialize(self.devnum, 
                                                   mode_id_dict[self.mode],
                                                   refsrc_id_dict[self.refsource]))
    
            # HH_GetHardwareInfo
            hw_model   = create_string_buffer(16)
            hw_partno  = create_string_buffer(8)
#             with self.lock:
#                 self._err(self.hhlib.HH_GetHardwareInfo(self.devnum,hw_model,hw_partno)) #/*this is only for information*/
#             self.hw_model   = hw_model.value
#             self.hw_partno  = hw_partno.value
#             if self.debug: print("Found Model %s Part No %s" % (self.hw_model, self.hw_partno))
            
            # HH_GetBaseResolution
            r = c_double()
            s = c_int()
            with self.lock:
                self._err(self.hhlib.HH_GetBaseResolution(self.devnum, byref(r), byref(s)))
            self.base_resolution = r.value # in picoseconds
            self.max_bin_steps = s.value
            
            # HH_GetNumOfInputChannels
            x = c_int()
            self._err(self.hhlib.HH_GetNumOfInputChannels(self.devnum, byref(x)))
            self.num_input_channels = x.value
            
            # HH_GetNumOfModules
            x = c_int()
            self._err(self.hhlib.HH_GetNumOfModules(self.devnum, byref(x)))
            self.num_modules = x.value
            
            ## SKIP: HH_GetModuleInfo
            ## SKIP: HH_GetModuleIndex
            ## SKIP: HH_GetHardwareDebugInfo
            
            # HH_Calibrate
            if self.debug: print( "HydraHarp Calibrating..." )
            with self.lock:
                self._err(self.hhlib.HH_Calibrate(self.devnum) )
    
    
            #self.CFDLevel     = [None,]*self.num_input_channels
            #self.CFDZeroCross = [None,]*self.num_input_channels
    
            
            ## HIST mode
            if mode == 'HIST':
                self.hist_len = self.SetHistoLen() #default length
                self.hist_data = [None]*self.num_input_channels
        
        except Exception as err:
            print("Failed to connect!!!", err)
            self.close()
            raise err

    def close(self):
        with self.lock:
            self._err(self.hhlib.HH_CloseDevice(self.devnum))

    def _err(self, retcode):
        if retcode < 0:
            err_buffer = create_string_buffer(40)
            self.hhlib.HH_GetErrorString(err_buffer, retcode)
            self.err_message = err_buffer.value.decode()
            raise IOError("HydraHarp Error {}: {}".format(retcode, self.err_message))
        return retcode

            
    def SetSyncDiv(self, div):
        """
        The sync divider must be used to keep the effective sync rate at values <= 12.5 MHz. It should only be used with sync
        sources of stable period. Using a larger divider than strictly necessary does not do great harm but it may result in slightly larger timing jitter. 
        The readings obtained with HH_GetCountRate are internally corrected for the divider setting and deliver the
        external (undivided) rate. The sync divider should not be changed while a measurement is running."""
        with self.lock:
            self._err(self.hhlib.HH_SetSyncDiv(self.devnum, int(div)))
    
    
    def SetSyncCFD(self, level, zerocross):
        """level and zerocross in integer millivolts"""
        with self.lock:
            self._err(self.hhlib.HH_SetSyncCFD(self.devnum, int(level), int(zerocross)))
            
    def SetSyncChannelOffset(self, value):
        "value: sync timing offset in ps"
        with self.lock:
            self._err(self.hhlib.HH_SetSyncChannelOffset(self.devnum, int(value)))
        
    def SetInputCFD(self, chan, level, zerocross):
        """level and zerocross in integer millivolts"""
        #self.CFDLevel[chan] = int(level)
        #self.CFDZeroCross[chan] = int(zerocross)
        if self.debug: print( "SetInputCFD {} {} {}".format( chan, level, zerocross))
        with self.lock:
            self._err(self.hhlib.HH_SetInputCFD(self.devnum, chan, int(level), int(zerocross)))
    
    def SetInputChannelOffset(self, chan, value):
        "value: sync timing offset in ps"
        assert 0 <= chan < self.num_input_channels
        with self.lock:
            self._err(self.hhlib.HH_SetInputChannelOffset(self.devnum, chan, int(value)))
    
    def SetInputChannelEnable(self, chan, enable):
        assert 0 <= chan < self.num_input_channels
        with self.lock:
            self._err(self.hhlib.HH_SetInputChannelEnable(
                self.devnum, chan, int(bool(enable))))

    def SetStopOverflow(self, stop_ofl=True, stopcount=STOPCNTMAX):
        with self.lock:
            self._err(self.hhlib.HH_SetStopOverflow( int(self.devnum), 
                                int(stop_ofl),int(stopcount)) )
    
    def SetBinning(self, binning):
        """
        Note: the binning code corresponds to repeated doubling, i.e.
            0 = 1x base resolution,
            1 = 2x base resolution,
            2 = 4x base resolution,
            3 = 8x base resolution, and so on.
        """
        with self.lock:
            self._err(self.hhlib.HH_SetBinning(self.devnum, int(binning)))

    def SetOffset(self):
        """This offset must not be confused with the input offsets in each channel that acts like a cable delay. In contrast, the offset
        here is subtracted from each start-stop measurement before it is used to either address the histogram channel to be incremented (in histogramming mode) or to be stored in a T3 mode record. The offset therefore has no effect in T2 mode and it
        has no effect on the relative timing of laser pulses and photon events. It merely shifts the region of interest where time difference data is to be collected. This can be useful e.g. in time-of-flight measurements where only a small time span at the far
        end of the range is of interest.        
        """
        pass
    
    def SetHistoLen(self, lencode=MAXLENCODE):
        """
        sets the histogram length based on length code *lencode*
        in range 0 to MAXLENCODE (default is  MAXLENCODE)
        returns the current length (time bin count) of histograms
        calculated as 1024 * (2^lencode)
        """
        lencode = int(lencode)
        assert 0 <= lencode <= MAXLENCODE
        x = c_int()
        with self.lock:
            self._err(self.hhlib.HH_SetHistoLen(self.devnum, lencode, byref(x)))
        self.hist_len = x.value
        return self.hist_len
        
        
    def ClearHistMem(self):
        with self.lock:
            self._err(self.hhlib.HH_ClearHistMem(self.devnum))
    
    ## SKIP: SETMeasControl
    
    def StartMeas(self, tacq):
        """tacq: acquisition time in integer milliseconds
                minimum = ACQTMIN
                maximum = ACQTMAX"""
        with self.lock:
            self._err(self.hhlib.HH_StartMeas(self.devnum, int(tacq)))
        
    def StopMeas(self):
        """Note: Can also be used before the acquisition time expires."""
        with self.lock:
            self._err(self.hhlib.HH_StopMeas(self.devnum))

    def CTCStatus(self):
        """
        returns the acquisition time state:
            False = acquisition time still running
            True = acquisition time has ended
        """
        status = c_int()
        with self.lock:
            self._err(self.hhlib.HH_CTCStatus(self.devnum, byref(status)))
        if status.value == 0: # not done
            return False
        else: # scanning done
            return True
    
    def check_done_scanning(self):
        return self.CTCStatus()
    
    ## SKIP GetHistogram (included in read_histogram_data)
    
    def read_histogram_data(self, channel=0, clear_after=False):
        channel = int(channel)
        if self.debug: print( "read_histogram_data channel %i" % channel)                
        self.hist_data[channel] = numpy.zeros(self.hist_len, dtype=numpy.uint32)
        with self.lock:
            self._err(self.hhlib.HH_GetHistogram(self.devnum, 
                                        self.hist_data[channel].ctypes.data_as(ctypes.POINTER(c_uint32)), 
                                        channel,
                                        int(bool(clear_after))))
        return self.hist_data[channel]
    
    def GetResolution(self):
        """returns the resolution at the current binning
        (histogram bin width) in ps,
        """
        r = c_double(0)
        with self.lock:
            self._err(self.hhlib.HH_GetResolution(self.devnum, byref(r)))
        self.resolution = r.value
        return self.resolution

    def GetSyncRate(self):
        """returns the current sync rate"""
        r = c_int(0)
        with self.lock:
            self._err(self.hhlib.HH_GetSyncRate(self.devnum, byref(r)))
        return r.value     
        
    def GetCountRate(self, chan):
        """returns the current count rate of this input channel
        
        Allow at least 100 ms after HH_Initialize or HH_SetSyncDivider to get a stable rate meter reading.
        Similarly, wait at least 100 ms to get a new reading. This is the gate time of the counters.
        """
        r = c_int(0)
        with self.lock:
            self._err(self.hhlib.HH_GetCountRate(self.devnum, chan, byref(r)))
        return r.value
    
    ## SKIP GetFlags
    
    def GetElapsedMeasTime(self):
        """
        returns the elapsed measurement time in ms
        
        Note: This can be used while a measurement is running 
        but also after it has stopped
        """
        x = c_double(0)
        with self.lock:
            self._err(self.hhlib.HH_GetElapsedMeasTime(self.devnum, byref(x)))
        return x.value
    
    ## SKIP GetWarnings
    
    ## SKIP GetWarningsText
    
    def GetSyncPeriod(self):
        """
        returning the sync period in ps
        
        // NEW SINCE V3.0
        
        note: This call only gives meaningful results while a measurement is running and after two sync periods have elapsed.
        The return value is undefined in all other cases. Accuracy is determined by single shot jitter and crystal tolerances
        """
        x = c_double(0)
        with self.lock:
            self._err(self.hhlib.HH_GetSyncPeriod(self.devnum, byref(x)))
        return x.value        
    
    #### For TTTR Mode
    
    # TODO
    
    #### For Continuous Mode
    
    # TODO 
    
    
    #### Helper functions
    
    def compute_hist_time_array(self):
        return numpy.arange(0, self.hist_len)*self.GetResolution()
        
