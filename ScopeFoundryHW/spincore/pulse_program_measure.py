'''
Created on Apr 4, 2022

@author: Benedikt Ursprung
'''

import numpy as np

from pyqtgraph.dockarea.DockArea import DockArea

from ScopeFoundry import Measurement, h5_io
from ScopeFoundryHW.spincore import PulseProgramGenerator, PulseBlasterChannel, us, ns


class TestPulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('my_param_1', unit='us', initial=1.0)
        self.settings.New('my_param_2', unit='ns', initial=500.0)

    def make_pulse_channels(self) -> [PulseBlasterChannel]:
        S = self.settings

        start_times = np.arange(2) * (S['my_param_1'] * us * 1.2)
        lengths = np.ones(2) * S['my_param_2'] * ns

        # DAQ
        chan_1 = self.new_channel('channel_name_1', start_times, lengths)

        return [chan_1]


class PulseProgramMeasure(Measurement):

    name = "pulse_program_measure"

    def setup(self):
        self.pulse_generator = TestPulseProgramGenerator(self)

    def setup_figure(self):
        self.ui = DockArea()
        self.ui.addDock(
            dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()

    def save_h5_data(self):
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(
            self, self.h5_file)
        self.pulse_generator.save_to_h5(self.h5_meas_group)
        self.h5_file.close()

    def run(self):
        self.pulse_generator.program_pulse_blaster_and_start()
        print(self.name, 'programmed')
