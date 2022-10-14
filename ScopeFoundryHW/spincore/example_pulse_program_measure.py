'''
Created on Apr 4, 2022

@author: Benedikt Ursprung
'''
import numpy as np
from pyqtgraph.dockarea.DockArea import DockArea

from ScopeFoundry import Measurement, h5_io
from ScopeFoundryHW.spincore import PulseProgramGenerator, ns, us


class ExamplePulseProgramGenerator(PulseProgramGenerator):

    def setup_additional_settings(self) -> None:
        self.settings.New('some_time', unit='us', initial=1.0)
        self.settings.New('some_duration', unit='ns', initial=500.0)

    def make_pulse_channels(self) -> None:
        S = self.settings
        start_times = np.arange(2) * (S['some_time'] * us)
        lengths = [S['some_duration'] * ns] * 2
        # assuming there are channels called 'channel_name_1' and 'channel_name_2'
        self.new_channel('channel_name_1', start_times, lengths)
        self.new_channel('channel_name_2', [1000, 2000, 3000],  [
                         S['some_duration'] * ns] * 3)
        self.new_channel(3, start_times, lengths)


class ExampleProgramMeasure(Measurement):

    name = "pulse_program_measure"

    def setup(self):
        self.pulse_generator = ExamplePulseProgramGenerator(self)
        self.data = {'x': np.arange(10)}

    def setup_figure(self):
        self.ui = DockArea()
        self.ui.addDock(
            dock=self.pulse_generator.New_dock_UI(), position='left')
        self.update_display()

    def save_h5_data(self):
        h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        h5_meas_group = h5_io.h5_create_measurement_group(self, h5_file)
        for k, v in self.data.items():
            h5_meas_group[k] = v
        self.pulse_generator.save_to_h5(h5_meas_group)
        h5_file.close()

    def run(self):
        self.pulse_generator.program_pulse_blaster_and_start()
        print(self.name, 'pulse_blaster programmed and started')
        print('collecting data')
