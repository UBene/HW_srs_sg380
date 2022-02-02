from crystaltech_dds import crystaltech_dds

VIS_PORT  = '/dev/ttyS3'
NIR1_PORT = '/dev/ttyS1'
NIR2_PORT = '/dev/ttyS1'

class crystaltech_aotf(object):

    def __init__(self, crystal='vis', debug=False):
        
        self.crystal = crystal.lower()
        self.debug = debug
        
        
        if self.crystal == 'vis':
            #42769 WO100813
            self.calibration_set = (+3.531e+02, -7.217e-01, +6.087e-04, -1.848e-07)
     	    self.port=VIS_PORT
            print ("visible crystal chosen!")
        elif self.crystal == 'nir1':
            #45005 WO100813
            #self.calibration_set = (+7.455e+02, -2.536e+00, +3.402e-03, -1.620e-06)
     	    self.port=NIR_PORT
            print ("Near IR 1 crystal chosen!")
        else:
            raise ValueError("crystal value not allowed:%s" % self.crystal)

        self.dds = crystaltech_dds(port=self.port, debug=self.debug)
        self.dds.set_calibration(*self.calibration_set)
        self.dds.modulation_enable()
            
        
    def set_wavelength(self, wl, channel=0):
        self.dds.set_wavelength(wl, channel)
        print ("wavelength = %g" % wl)
    
    def get_wavelength(self, channel=0):
        return self.dds.get_wavelength()
        
    def set_amplitude(self, amp, channel=0):
        self.dds.set_amplitude(amp, channel)
        
    def get_amplitude(self, channel=0):
        return self.dds.get_amplitude(channel)
            
    def close(self):
        self.dds.close()

