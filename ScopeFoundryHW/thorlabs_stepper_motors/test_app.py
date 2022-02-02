from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

class ThorlabsStepperTestApp(BaseMicroscopeApp):
    
    name="thorlab_stepper_test_app"
    
    def setup(self):
        from ScopeFoundryHW.thorlabs_stepper_motors.thorlabs_stepper_controller_hw import ThorlabsStepperControllerHW
        self.add_hardware(ThorlabsStepperControllerHW(self, ax_names='xyz'))
        
        from ScopeFoundryHW.thorlabs_stepper_motors.thorlabs_stepper_raster import ThorlabsStepperDelay2DScan
        self.add_measurement(ThorlabsStepperDelay2DScan(self))
        
if __name__ == '__main__':
    import sys
    app = ThorlabsStepperTestApp(sys.argv)
    sys.exit(app.exec_())    
        