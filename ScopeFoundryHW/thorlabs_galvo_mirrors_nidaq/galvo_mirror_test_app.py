'''
Created on Sep 17, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry.base_app import BaseMicroscopeApp


class App(BaseMicroscopeApp):

    name = 'galvo_mirrors_test_app'

    def setup(self):

        from ScopeFoundryHW.thorlabs_galvo_mirrors_nidaq import GalvoMirrorsHW

        # NOTE max_step_degree * rate defines the biggest step rate without breaking the stage
        self.add_hardware(GalvoMirrorsHW(self, max_step_degree=0.2, rate=1e3))

        try:
            from ScopeFoundryHW.thorlabs_galvo_mirrors_nidaq import \
                GalvoMirrorAPDScanMeasure
            self.add_measurement(GalvoMirrorAPDScanMeasure(self))
        except ImportError:
            # requires ScopeFoundry.scanning
            pass


if __name__ == '__main__':
    import sys
    app = App(sys.argv)
    sys.exit(app.exec_())
