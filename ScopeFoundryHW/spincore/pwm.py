'''
Created on Apr 4, 2022

@author: Benedikt Ursprung
'''
from pyqtgraph.dockarea.DockArea import DockArea

from ScopeFoundry import Measurement, h5_io
from ScopeFoundryHW.spincore import PulseProgramGenerator, ns, us


class PWMProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('duty_cycle', unit='%', initial=50, vmax=100, vmin=0)
        self.settings.New('frequency', unit='Hz', initial=500.0, vmin=0)

    def make_pulse_channels(self) -> None:
        period_ns = 1e9 / self.settings['frequency']
        up_ns = (self.settings['duty_cycle'] / 100) * period_ns
        self.settings['all_off_padding'] = period_ns - up_ns
        self.new_channel(0, [0], [up_ns])
        self.new_channel(1, [0], [up_ns])
        self.new_channel(2, [0], [up_ns])
        self.new_channel(3, [0], [up_ns])
        self.new_channel(4, [0], [up_ns])
        self.new_channel(5, [0], [up_ns])


class PMW(Measurement):

    name = "pwm"

    def setup(self):
        self.pulse_generator = PWMProgramGenerator(self)
        self.add_operation('save h5', self.save_h5_data)

    def setup_figure(self):
        self.ui = DockArea()
        self.ui.addDock(
            dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()

    def save_h5_data(self):
        h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        h5_meas_group = h5_io.h5_create_measurement_group(self, h5_file)
        self.pulse_generator.save_to_h5(h5_meas_group)
        h5_file.close()
