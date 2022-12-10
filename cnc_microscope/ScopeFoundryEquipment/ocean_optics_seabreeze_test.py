import ctypes
from ctypes import c_int, c_int64, c_uint, c_byte, c_ubyte, c_short, c_double, c_float, c_long, c_void_p
from ctypes import pointer, byref, windll, cdll
import time
import numpy as np
import os


sblibpath = r"C:\Program Files\Ocean Optics\SeaBreeze\Library\SeaBreeze.dll"

print sblibpath
S = sbapi = cdll.LoadLibrary(sblibpath)

S.sbapi_initialize()

ndevs = S.sbapi_probe_devices()

print "ndevs", ndevs

ndev_ids = S.sbapi_get_number_of_device_ids()

print "ndev_ids", ndev_ids

dev_ids = np.zeros( 256, dtype=np.int64) # long

print S.sbapi_get_device_ids( dev_ids.ctypes.data, 255 )
print "dev_ids", dev_ids[:10]


dev_id = int(dev_ids[0])

err_code = c_long(0)

#S.sbapi_open_device.arg_types = [c_int, c_void_p]

retcode = S.sbapi_open_device(dev_id, byref(err_code))
if retcode != 0: handle_sb_err(err_code)

INT_TIME_MICROS = 1000000


# get device type

dev_type_buffer = ctypes.create_string_buffer(' ', 256)

S.sbapi_get_device_type(dev_id, byref(err_code), dev_type_buffer, 256)

dev_type = str(dev_type_buffer.raw).strip('\x00')
print repr(dev_type)

# get features for device id
print "# features", S.sbapi_get_number_of_spectrometer_features(dev_id, byref(err_code))
feature_ids = -1* np.ones( 256, dtype=int)
n_features = S.sbapi_get_spectrometer_features(dev_id, byref(err_code), feature_ids.ctypes.data, 256)

feature_id = int(feature_ids[0])

print "features", n_features, feature_ids[:10]

# set trigger mode
# 	Mode (Input) a trigger mode (0 = normal, 1 = software, 2 = synchronization, 3 = external hardware, etc - check your particular spectrometer's Data Sheet)

S.sbapi_spectrometer_set_trigger_mode(dev_id,feature_id, byref(err_code), 0)		


# get minimum integration time
min_int_time = S.sbapi_spectrometer_get_minimum_integration_time_micros(dev_id, feature_id, byref(err_code) )
print "min_int_time", repr(min_int_time), "microsec"


# get spectrum parameters

Nspec = S.sbapi_spectrometer_get_formatted_spectrum_length( dev_id, feature_id, byref(err_code) )

print Nspec

wavelengths = np.zeros( Nspec, dtype=float )

S.sbapi_spectrometer_get_wavelengths(dev_id, feature_id, byref(err_code), wavelengths.ctypes.data, Nspec)

print wavelengths

# read dark pixels

ndark = S.sbapi_spectrometer_get_electric_dark_pixel_count(dev_id, feature_id, byref(err_code))

dark_indices = np.zeros(ndark, dtype=int)

S.sbapi_spectrometer_get_electric_dark_pixel_indices(dev_id, feature_id, byref(err_code), dark_indices.ctypes.data, ndark)

print "dark", ndark, dark_indices

# set integration time
# unsigned long
S.sbapi_spectrometer_set_integration_time_micros(dev_id, feature_id, byref(err_code), INT_TIME_MICROS)

# get spectrum
spectrum = np.zeros(Nspec, dtype=float)

print "acquiring..."
S.sbapi_spectrometer_get_formatted_spectrum(dev_id, feature_id, byref(err_code), spectrum.ctypes.data, Nspec)
print "done"

print spectrum



retcode = S.sbapi_close_device(dev_id, byref(err_code))
print retcode

S.sbapi_shutdown()


import pylab as pl

pl.plot(wavelengths[13:], spectrum[13:])
pl.show()

# TODO
## read out electric dark pixels
## 

def handle_sb_err(err_code):
	print "Err %i" % err_code, S.sbapi_get_error_string(err_code)
	raise ValueError()