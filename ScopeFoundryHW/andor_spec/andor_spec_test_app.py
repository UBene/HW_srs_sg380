from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.andor_spec.andor_spec_hw import AndorShamrockSpecHW

class ActonSpecTestApp(BaseMicroscopeApp):
    
    name = 'acton_spec_test_app'
    
    def setup(self):
        hw = self.add_hardware(AndorShamrockSpecHW(self))
                
if __name__ == '__main__':
    import sys
    app = ActonSpecTestApp(sys.argv)
    app.exec_()