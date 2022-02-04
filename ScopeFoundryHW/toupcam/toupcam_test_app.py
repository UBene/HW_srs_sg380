from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.toupcam.toupcam_live_measure import ToupCamLiveMeasure
from ScopeFoundryHW.toupcam.toupcam_hw import ToupCamHW
class ASITestApp(BaseMicroscopeApp):
    
    name = 'toupcam_test_app'
    
    def setup(self):
        hw = self.add_hardware(ToupCamHW(self))
        self.add_measurement(ToupCamLiveMeasure(self))
        
                
if __name__ == '__main__':
    import sys
    app = ASITestApp(sys.argv)
    app.exec_()