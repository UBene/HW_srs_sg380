import uc480
import pylab as pl

# create instance and connect to library
cam = uc480.uc480()

# connect to first available camera
cam.connect()
cam.get_hw_master_gain_factor()

# take a single image
img = cam.acquire()

# clean up
cam.disconnect()

pl.imshow(img, cmap='gray')
pl.colorbar()
pl.show()