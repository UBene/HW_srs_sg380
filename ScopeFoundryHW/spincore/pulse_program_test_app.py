'''
Created on Mar 21, 2022

@author: Benedikt Ursprung
'''


from ScopeFoundry.base_app import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):        
        from ScopeFoundryHW.spincore.pulse_blaster_hw import PulseBlasterHW
        named_channel_kwargs = [
            {
            "name":'my_named_channel',
            'initial':1, 
            'colors':['y'],
            'description':'a physical output channel that can be referenced by its name'           
            }
        ]
        
        self.add_hardware(PulseBlasterHW(self,
                                         named_channels_kwargs=named_channel_kwargs,
                                         clock_frequency_Hz=500_000_000,
                                         short_pulse_bit_num=21))
        from ScopeFoundryHW.spincore.example_pulse_program_measure import \
            ExampleProgramMeasure
        self.add_measurement(ExampleProgramMeasure(self))
        from ScopeFoundryHW.spincore.pwm import PMW
        self.add_measurement(PMW(self))


if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
