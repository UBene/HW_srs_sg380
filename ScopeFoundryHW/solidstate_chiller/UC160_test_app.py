from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundryHW.solidstate_chiller.UC160_hw import UC160HW


class UC160TestApp(BaseMicroscopeApp):
    
    name = 'UC160_test_app'
    
    def setup(self):
        hw = self.add_hardware(UC160HW(self))
        
                
if __name__ == '__main__':
    import sys
    app = UC160TestApp(sys.argv)
    app.exec_()