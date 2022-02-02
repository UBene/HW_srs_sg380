import ctypes
from ctypes import windll, byref, c_uint32, c_double
import threading

class ThorlabsPAX1000_Polarimeter(object):

    thorlib_path = r'C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLPAX_64.dll' 
    
    
    def _err(self, retcode):
        if retcode < 0:
            err_buffer = ctypes.create_string_buffer(1024)
            self.dll.TLPAX_errorMessage(self.inst_handle, retcode, err_buffer)
            self.err_message = err_buffer.value.decode()
            raise IOError("TLPAX Error {}: {}".format(retcode, self.err_message))
        return retcode
    
    def __init__(self, auto_find=True, rsrc_name = None, auto_find_num=0, debug=False):
        self.debug = debug
        self.lock = threading.Lock()
        self.sessionHandle = ctypes.c_uint32(0)
        self.dll = windll.LoadLibrary(self.thorlib_path)

        self.inst_handle = c_uint32(0)
        
        if auto_find:
            num_devices = c_uint32(0)
            self.dll.TLPAX_findRsrc(0, byref(num_devices))
            #self.find_instrument()
            if num_devices.value == 0:
                raise IOError("No device found")
            
            rsrc_name_buf = ctypes.create_string_buffer(b"", size=1024)
            with self.lock:
                self.dll.TLPAX_getRsrcName(0, auto_find_num, rsrc_name_buf)
            rsrc_name_bytes = rsrc_name_buf.value
            #print(rsrc_name_bytes)
            
        else:
            rsrc_name_bytes = rsrc_name.encode()

        # ViStatus TLPAX_init (ViRsrc resourceName, ViBoolean IDQuery, ViBoolean resetDevice, ViPSession instrumentHandle); 
        self._err(self.dll.TLPAX_init(rsrc_name_bytes, 
                                          False, 
                                          False, 
                                          byref(self.inst_handle)))
        
        
        
        model_name = ctypes.create_string_buffer(b"", size=1024)
        serial_num = ctypes.create_string_buffer(b"", size=1024)
        firmware = ctypes.create_string_buffer(b"", size=1024)

        self._err(self.dll.TLPAX_identificationQuery(self.inst_handle,0,
                                                     model_name, 
                                                     serial_num,
                                                     firmware))
        

        driver_version = ctypes.create_string_buffer(b"", size=1024)
        self._err(self.dll.TLPAX_revisionQuery(self.inst_handle, driver_version, 0))

        print(self.inst_handle.value, model_name.value, serial_num.value, firmware.value, driver_version.value)


    def close(self):
        self._err(self.dll.TLPAX_close(self.inst_handle))

    @classmethod
    def find_instrument(cls):
        num_devices = c_uint32(1)
        cls.dll = windll.LoadLibrary(cls.thorlib_path)
        cls.dll.TLPAX_findRsrc(0, byref(num_devices))
        #print(num_devices.value)
        
        
        rsrc_name = ctypes.create_string_buffer(b"", size=1024)
        model_name = ctypes.create_string_buffer(b"", size=1024)
        serial_num = ctypes.create_string_buffer(b"", size=1024)
        is_dev_avail = ctypes.c_bool(False)
        
        for i in range(num_devices.value):
            cls.dll.TLPAX_getRsrcInfo(0, i, model_name, serial_num, 0, byref(is_dev_avail) )
            cls.dll.TLPAX_getRsrcName(0, i, rsrc_name)
            print(i, rsrc_name.value, model_name.value, serial_num.value, is_dev_avail.value)


    meas_modes = ["IDLE", 
                  "HALF_512", "HALF_1024", "HALF_2048", 
                  "FULL_512", "FULL_1024", "FULL_2048", 
                  "DOUBLE_512", "DOUBLE_1024","DOUBLE_2048"]
    #define TLPAX_MEASMODE_IDLE         (0)   ///< Idle, no measurements are taken
    #define TLPAX_MEASMODE_HALF_512     (1)   ///< 0.5 revolutions for one measurement, 512 points for FFT
    #define TLPAX_MEASMODE_HALF_1024    (2)   ///< 0.5 revolutions for one measurement, 1024 points for FFT
    #define TLPAX_MEASMODE_HALF_2048    (3)   ///< 0.5 revolutions for one measurement, 2048 points for FFT
    #define TLPAX_MEASMODE_FULL_512     (4)   ///< 1 revolution for one measurement, 512 points for FFT
    #define TLPAX_MEASMODE_FULL_1024    (5)   ///< 1 revolution for one measurement, 1024 points for FFT
    #define TLPAX_MEASMODE_FULL_2048    (6)   ///< 1 revolution for one measurement, 2048 points for FFT
    #define TLPAX_MEASMODE_DOUBLE_512   (7)   ///< 2 revolutions for one measurement, 512 points for FFT
    #define TLPAX_MEASMODE_DOUBLE_1024  (8)   ///< 2 revolutions for one measurement, 1024 points for FFT
    #define TLPAX_MEASMODE_DOUBLE_2048  (9)   ///< 2 revolutions for one measurement, 2048 points for FFT



    def get_measurement_mode(self):
        mode = c_uint32()
        with self.lock:
            self._err(self.dll.TLPAX_getMeasurementMode(self.inst_handle, byref(mode)))
        mode_str = self.meas_modes[mode.value]
        return mode_str
        
    def set_measurement_mode(self, mode_str):
        if self.debug:
            print("set_measurement_mode -->", mode_str)
        mode_id = self.meas_modes.index(mode_str)
        with self.lock:
            self._err(self.dll.TLPAX_setMeasurementMode(self.inst_handle, mode_id))
        
    def get_basic_scan_rate(self):
        """
        Reads the basic scan rate. According to the measurement mode each
        half rotation each full rotation or two full rotations of the waveplate
        produce one measurement data set (scan). The basic scan rate describes
        how many half rotation scans are possible per second.
        returns float of basic scan rate in [1/s]
        """
        
        bsr = c_double()
        with self.lock:
            self._err(self.dll.TLPAX_getBasicScanRate(self.inst_handle, byref(bsr)))
        return bsr.value
    


    def get_scan(self):
        with self.lock:
            scan = dict()
            scan_id = c_uint32(0)
            self._err(self.dll.TLPAX_getLatestScan(self.inst_handle, byref(scan_id)))        
            try:
                ts = c_uint32()
                
                #The timestamp of the scan in milli seconds since power up of the polarimeter device. 
                self._err(self.dll.TLPAX_getTimeStamp(self.inst_handle, scan_id, byref(ts)))
                scan['timestamp'] = ts.value
                
                azimuth = c_double()
                ellipticity = c_double()
                self._err(self.dll.TLPAX_getPolarization(self.inst_handle, scan_id, 
                                                         byref(azimuth), 
                                                         byref(ellipticity)))
                scan['azimuth'] = azimuth.value
                scan['ellipticity'] = ellipticity.value
                
                tp = c_double(); pp = c_double(); up = c_double()
                self._err(self.dll.TLPAX_getPower(self.inst_handle, scan_id, 
                                             byref(tp),
                                             byref(pp),
                                             byref(up)))
                scan['total_power'] = tp.value
                scan['polarized_power'] = pp.value
                scan['unpolarized_power'] = up.value
                
                DOP = c_double(); DOLP = c_double(); DOCP = c_double();
                self._err(self.dll.TLPAX_getDOP(self.inst_handle,scan_id,
                                                byref(DOP), byref(DOLP), byref(DOCP)))
                scan['DOP'] = DOP.value # The degree of polarisation value (DOP). Value 1.0 = 100% DOP.
                scan['DOLP'] = DOLP.value # The degree of linear polarisation value (DOLP). Value 1.0 = 100% DOLP. 
                scan['DOCP'] = DOCP.value # The degree of circular polarisation value (DOCP). Value 1.0 = 100% DOCP.
                
#                 S = [ c_double(1.0), c_double(), c_double(), c_double()]
#                 self._err(self.dll.TLPAX_getStokes(self.inst_handle,scan_id,
#                                                 byref(S[0]), byref(S[1]), byref(S[2]), byref(S[3])))
#                 scan['Stokes'] = [x.value for x in S]
#                 
#                 S = [ c_double(1), c_double(), c_double(), c_double()]
#                 self._err(self.dll.TLPAX_getStokes(self.inst_handle,scan_id,
#                                                 byref(S[1]), byref(S[2]), byref(S[3])))
#                 scan['StokesNormalized'] = [x.value for x in S]

                
            finally:
                self._err(self.dll.TLPAX_releaseScan(0, scan_id))
        return scan
            
    def get_wavelength_limits(self):
        """
        get wavelength limits in nm
        returns (min_wl, max_wl)
        """
        wl_min = c_double()
        wl_max = c_double()
        with self.lock:
            self._err(self.dll.TLPAX_getWavelengthLimits(self.inst_handle, byref(wl_min), byref(wl_max)))
        return wl_min.value*1e9, wl_max.value*1e9
        
        
        
            
    def get_wavelength(self):
        """Get the user wavelength in nm. """
        # ViStatus TLPAX_getWavelength (ViSession instrumentHandle, ViPReal64 wavelength); 
        wl = c_double()
        with self.lock:
            self._err(self.dll.TLPAX_getWavelength(self.inst_handle, byref(wl)))
        return wl.value*1e9 # convert from m --> nm
    
    def set_wavelength(self, wl_nm):
        """
        Set the users wavelength in nanometer [nm]. The wavelength value is required
        for calculating correct measurement data.
        """
        with self.lock:
            self._err(self.dll.TLPAX_setWavelength(self.inst_handle, c_double(wl_nm*1e-9)))



if __name__ == '__main__':
    #ThorlabsPAX1000_Polarimeter.find_instrument()
    pax = ThorlabsPAX1000_Polarimeter(auto_find=True,auto_find_num=0)# rsrc_name="USB::0x1313::0x8031::M00559829::INSTR")
    print("mode", pax.get_measurement_mode())
    print("setting", pax.set_measurement_mode("HALF_1024"))
    print("mode", pax.get_measurement_mode())
    print("basic scan rate", pax.get_basic_scan_rate())
    print("wl range", pax.get_wavelength_limits())
    print("wl", pax.get_wavelength())
    print("wl set", pax.set_wavelength(1080))
    print("wl", pax.get_wavelength())
    import pprint
    pprint.pprint(pax.get_scan())
    #import timeit
    #t = timeit.timeit("pax.get_scan()", globals=globals(), number=100000)
    #print(t)
    
    
    
    