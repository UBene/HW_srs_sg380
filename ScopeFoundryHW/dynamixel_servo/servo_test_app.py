from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo_hw import DynamixelXServosHW
from ScopeFoundryHW.dynamixel_servo.dynamixel_filter_wheel_hw import DynamixelFilterWheelHW


class ServoTestApp(BaseMicroscopeApp):
    
    name = 'servo_test_app'
    
    def setup(self):
        
        servos = self.add_hardware(DynamixelXServosHW(self, devices=dict(reflector_wheel=10,)))

        self.add_hardware(DynamixelFilterWheelHW(self, name='reflector_wheel',
                                        named_positions={'empty':  (90, "lightgreen"),
                                                         'mirror': (180, 'yellowgreen'),
                                                         'glass':  (270, "lime"),
                                                         },))
                                                                                  
        servos.settings['port'] = 'COM10'
        servos.settings['connected'] = True

        
if __name__ == '__main__':

    import sys
    app = ServoTestApp(sys.argv)
    # app.qtapp.setStyle('Fusion')
    sys.exit(app.exec_())
