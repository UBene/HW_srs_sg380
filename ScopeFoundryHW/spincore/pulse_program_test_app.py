'''
Created on Mar 21, 2022

@author: Benedikt Ursprung
'''


from ScopeFoundry.base_app import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):
        channel_settings = [
            dict(name='channel_name_1', initial=1, colors=['r'],
                 description='a pysical output channel'),
            dict(name='channel_name_2', initial=2, colors=['b'],
                 description='another pysical output channel'),
        ]
        from ScopeFoundryHW.spincore.pulse_blaster_hw import PulseBlasterHW
        self.add_hardware(PulseBlasterHW(self,
                                         channel_settings=channel_settings,
                                         clock_frequency_Hz=500_000_000,
                                         short_pulse_bit_num=21))
        from ScopeFoundryHW.spincore.example_pulse_program_measure import \
            ExampleProgramMeasure
        self.add_measurement(ExampleProgramMeasure(self))


if __name__ == '__main__':
    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
