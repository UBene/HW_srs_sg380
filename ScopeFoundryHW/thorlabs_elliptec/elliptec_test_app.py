from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.thorlabs_elliptec.elliptec_hw import ThorlabsElliptecSingleHW,\
    ThorlabsElliptcMultiHW

class ElliptecTestApp(BaseMicroscopeApp):
    
    name = 'elliptec_test_app'
    
    def setup(self):
        
        self.add_hardware(ThorlabsElliptecSingleHW(self))
        
        self.add_hardware(ThorlabsElliptcMultiHW(self))
        
if __name__ == '__main__':
    import sys
    app = ElliptecTestApp(sys.argv)
    app.exec_()