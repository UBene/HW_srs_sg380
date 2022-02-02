from ScopeFoundry import BaseMicroscopeApp

class TestApp(BaseMicroscopeApp):
    
    name = 'thorlabs_integraged_stepper_motor_test_app'
    
    def setup(self):
        
        from ScopeFoundryHW.thorlabs_integrated_stepper.thorlabs_integrated_stepper_motor_hw import ThorlabsIntegratedStepperMottorHW
        self.add_hardware(ThorlabsIntegratedStepperMottorHW(self))
        
if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    app.exec_()