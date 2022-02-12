from ScopeFoundry import BaseMicroscopeApp

class TestApp(BaseMicroscopeApp):

    name = 'test_app'
    
    def setup(self):
        
        from ScopeFoundryHW.thorlabs_ell6k_dual_position_slider import ELL6KDualPositionSliderHW
        self.add_hardware(ELL6KDualPositionSliderHW(self))

if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())