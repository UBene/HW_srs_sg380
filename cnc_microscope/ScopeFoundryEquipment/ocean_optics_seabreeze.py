import ctypes
from ctypes import c_long, byref
import numpy as np
import threading
import time

SEABREEZE_DLL_PATH = r"C:\Program Files\Ocean Optics\SeaBreeze\Library\SeaBreeze.dll"

_S = sbapi = ctypes.cdll.LoadLibrary(SEABREEZE_DLL_PATH)

TRIG_NORMAL = 0
TRIG_SOFTWARE = 1
TRIG_SYNC = 2
TRIG_EXT = 3


# NOTE errors are not checked at this time

class OceanOpticsSpectrometer(object):

    def __init__(self, trigger_mode = TRIG_NORMAL, debug=False):
        
        self.debug = debug

        self.trigger_mode = trigger_mode
        self.err_code = err_code = c_long(0)
        
        _S.sbapi_initialize()

        # get total number of devices, will pick the first one
        ndevs = _S.sbapi_probe_devices()
        ndev_ids = _S.sbapi_get_number_of_device_ids()
        
        if ndev_ids < 1:
            raise IOError("No OceanOptics devices found")
        if ndev_ids > 1:
            print("more than one device attached. Will pick the first one")

        if self.debug: print( "ndevs", ndevs, ndev_ids)
        
        #get dev_id
        dev_ids = np.empty( ndev_ids, dtype=ctypes.c_long) # long
        
        _S.sbapi_get_device_ids( dev_ids.ctypes, ndev_ids )
        
        if debug: print("dev_ids", dev_ids)

        self.dev_id = dev_id = int(dev_ids[0])
        if debug: print("dev_id", dev_id)
        
        # open device
        retcode = _S.sbapi_open_device(dev_id, byref(err_code))
        if retcode != 0: self._handle_sbapi_error()

        # get device type
        dev_type_buffer = ctypes.create_string_buffer(b'', 256)
        _S.sbapi_get_device_type(dev_id, byref(err_code), dev_type_buffer, 256)
        self.dev_type = dev_type_buffer.raw.strip(b'\x00').decode()
        if debug: print("dev_type", repr(self.dev_type))

        # get features for device, will pick the first one
        n_features = _S.sbapi_get_number_of_spectrometer_features(int(self.dev_id), byref(err_code))
        print(repr(n_features), err_code.value)
        self._handle_sbapi_error() 
        print(repr(n_features))
        feature_ids = np.empty( n_features, dtype=int)
        print(_S.sbapi_get_spectrometer_features(dev_id, byref(err_code), feature_ids.ctypes, n_features))
        self.feature_id = feature_id = int(feature_ids[0])
        if debug: print("features", n_features, feature_ids)

        # set trigger mode
        #   Mode (Input) a trigger mode
        # (0 = normal, 1 = software, 2 = synchronization, 3 = external hardware, etc
        # - check your particular spectrometer's Data Sheet)
        _S.sbapi_spectrometer_set_trigger_mode(dev_id,feature_id, byref(err_code), self.trigger_mode)       

        # get minimum integration time
        self.min_int_time = _S.sbapi_spectrometer_get_minimum_integration_time_micros(dev_id, feature_id, byref(err_code) )
        if debug: print("min_int_time", self.min_int_time, "microsec")
        
        # get spectrum parameters
        self.Nspec = Nspec = _S.sbapi_spectrometer_get_formatted_spectrum_length( dev_id, feature_id, byref(err_code) )
        self.wavelengths = np.zeros( Nspec, dtype=float )
        _S.sbapi_spectrometer_get_wavelengths(dev_id, feature_id, byref(err_code), self.wavelengths.ctypes, Nspec)
        if debug: print(Nspec, self.wavelengths[[0,1,-2,-1]])
        
        # read dark pixels
        ndark = _S.sbapi_spectrometer_get_electric_dark_pixel_count(dev_id, feature_id, byref(err_code))
        self.dark_indices = np.zeros(ndark, dtype=int)
        _S.sbapi_spectrometer_get_electric_dark_pixel_indices(dev_id, feature_id, byref(err_code), self.dark_indices.ctypes, ndark)
        if debug: print("dark", ndark, self.dark_indices)

        # set integration to minimum by default
        self.int_time = self.min_int_time
        _S.sbapi_spectrometer_set_integration_time_micros(dev_id, feature_id, byref(err_code), self.int_time)
    
        self.spectrum = np.zeros(Nspec, dtype=float)
                
    def close(self):
        _S.sbapi_close_device(self.dev_id, byref(self.err_code))
        _S.sbapi_shutdown()
    
    def set_integration_time(self,int_time):
        """ Set the integration time in microseconds"""
        assert int_time > self.min_int_time
        self.int_time = int(int_time)
        _S.sbapi_spectrometer_set_integration_time_micros(
            self.dev_id, self.feature_id, byref(self.err_code), self.int_time)

            
    def set_integration_time_sec(self,int_time):
        return self.set_integration_time(int_time*1e6)
    
    def acquire_spectrum(self):
        _S.sbapi_spectrometer_get_formatted_spectrum(self.dev_id, self.feature_id, byref(self.err_code), self.spectrum.ctypes, self.Nspec)
        return self.spectrum

    def _handle_sbapi_error(self):
        if self.err_code.value == 0:
            return
        error_str_buffer = ctypes.create_string_buffer(' ', 256)
        error_str = str(error_str_buffer.raw).strip('\x00')
        _S.sbapi_get_error_string(self.error_code)
        raise IOError(error_str)

        
    def start_threaded_acquisition(self):
        self.acq_thread = threading.Thread(target=self.acquire_spectrum)
        self.acq_thread.start()
        self.t_start = time.time()

    def is_threaded_acquisition_complete(self):
        return not self.acq_thread.is_alive()
    
    def threaded_time_elapsed_remaining(self):
        now = time.time()
        time_elapsed = now - self.t_start
        time_remaining = self.int_time - time_elapsed
        return time_elapsed, time_remaining
        
if __name__ == '__main__':
    # Live testing
    import pylab as pl
    
    TEST_INT_TIME = 1e6 # microseconds
    
    
    oospec = OceanOpticsSpectrometer(debug=True)
    
    oospec.set_integration_time(TEST_INT_TIME)
    
    fig = pl.figure(1)
    ax = fig.add_subplot(111)
    ax.set_title("(%i,%i) %s" % (oospec.dev_id, oospec.feature_id, oospec.dev_type))
    
    oospec.acquire_spectrum()
    
    plotline, = pl.plot( oospec.wavelengths, oospec.spectrum )
    
    oospec.start_threaded_acquisition()
    
    def update_fig(ax):
        if oospec.is_threaded_acquisition_complete():
            #print "new data!"
            plotline.set_ydata( oospec.spectrum )
            oospec.start_threaded_acquisition()
            fig.canvas.draw()
        else:
            print(oospec.threaded_time_elapsed_remaining())
    
    timer = fig.canvas.new_timer( interval= 250)
    timer.add_callback( update_fig, ax)
    timer.start()
    
    #fig.show()
    pl.show()