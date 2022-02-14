from ScopeFoundry import BaseMicroscopeApp

class TestApp(BaseMicroscopeApp):

    name = 'spec_test_app'
    
    def setup(self):
        
        from ScopeFoundryHW.pi_spec import PISpectrometerHW
        self.add_hardware(PISpectrometerHW(self))
        

if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
