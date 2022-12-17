'''
Created on Sep 17, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.nidaqmx.galvo_mirrors.galvo_mirrors_hw import GalvoMirrorsHW
from ScopeFoundryHW.nidaqmx.galvo_mirrors.galvo_mirror_2d_apd_slow_scan import GalvoMirrorAPDScanMeasure


class App(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):

        self.add_hardware(GalvoMirrorsHW(self))
        self.add_measurement(GalvoMirrorAPDScanMeasure(self))


if __name__ == '__main__':
    import sys
    app = App(sys.argv)
    sys.exit(app.exec_())
