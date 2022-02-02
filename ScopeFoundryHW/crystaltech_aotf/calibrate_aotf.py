from __future__ import division

from equipment.crystaltech_dds import CrystalTechDDS
from equipment.ocean_optics_seabreeze import OceanOpticsSpectrometer
import pylab as pl
import time
import numpy as np

dds = CrystalTechDDS(comm="serial", port="COM1", debug=True)

dds.modulation_enable()

dds.set_amplitude(12000)
print dds.get_amplitude()

dds.set_frequency(112.0)
print dds.get_frequency()



oospec = OceanOpticsSpectrometer(debug=True)
	
oospec.set_integration_time(0.1e6)
fig = pl.figure(1)
ax = fig.add_subplot(111)

for ii, freq in enumerate(np.arange(80,160,2.5)):
    dds.set_frequency(freq)
    time.sleep(0.1)
    oospec.acquire_spectrum()

    plotline, = pl.plot( oospec.wavelengths, oospec.spectrum +4000*ii)#, color=(ii/150.,)*3)


dds.close()

pl.show()
