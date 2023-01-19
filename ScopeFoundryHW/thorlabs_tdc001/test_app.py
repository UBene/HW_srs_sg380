from ScopeFoundry.base_app import BaseMicroscopeApp

class TestApp(BaseMicroscopeApp):
    
    name="dc_servo_test_app"
    
    def setup(self):
        from ScopeFoundryHW.thorlabs_tdc001.dc_servo_hw import TDC001DCServoHW
        self.add_hardware(TDC001DCServoHW(self))
        
if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())    
        