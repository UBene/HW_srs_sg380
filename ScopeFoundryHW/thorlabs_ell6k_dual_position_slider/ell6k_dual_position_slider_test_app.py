from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.thorlabs_ell6k.ell6k_dual_position_slider import ELL6KDualPositionSliderHW

class TestApp(BaseMicroscopeApp):
    
    name = 'dual_slider_test_app'
    
    def setup(self):
        
        self.add_hardware(ELL6KDualPositionSliderHW(self))
        
        
if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    app.exec_()