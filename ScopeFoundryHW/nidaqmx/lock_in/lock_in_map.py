'''
Created on April 11, 2022

@author: Benedikt Ursprung
'''


import numpy as np
from ScopeFoundry.scanning.base_raster_scan import BaseRaster2DScan


class LockIn2dMap(BaseRaster2DScan):
    '''
    two counters active when corresponding gate is high.

    We are abusing a NIDAQ pulse width measurement, where the 
    pulse width become gate by setting the timebase=1Hz and clock ticks are replaced 
    by the photon counts.
    '''

    name = "lock_in_2d_map"


    def run(self):
        S = self.settings

        self.imag_map = np.zeros(self.scan_shape)

        DAQ = self.app.hardware['lock_in']

        self.data = {'analog': [],
                     'counts': [],
                     'map': []}