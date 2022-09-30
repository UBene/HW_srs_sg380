'''
Created on Sep 17, 2021

@author: lab
'''
from ScopeFoundry.base_app import BaseMicroscopeApp


class APP(BaseMicroscopeApp):

    name = 'test_app'

    def setup(self):
        channel_settings = [
        dict(name='channel_name_1', initial=1, colors=(255, 255, 255, 40),
                 description='a pysical output channel'),
        dict(name='channel_name_2', initial=2, colors=(255, 255, 255, 40),
                 description='another pysical output channel'),
        ]
        from ScopeFoundryHW.spincore.pulse_blaster_hw import PulseBlasterHW
        self.add_hardware(PulseBlasterHW(self, channel_settings=channel_settings))
        from ScopeFoundryHW.spincore.pulse_program_measure import PulseProgramMeasure
        self.add_measurement(PulseProgramMeasure(self))


if __name__ == '__main__':
    import sys
    app = APP(sys.argv)
    sys.exit(app.exec_())
