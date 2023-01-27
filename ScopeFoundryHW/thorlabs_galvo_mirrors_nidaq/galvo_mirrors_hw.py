from ScopeFoundry import HardwareComponent
import numpy as np

import nidaqmx
from nidaqmx.constants import VoltageUnits, AcquisitionType, Edge
from functools import partial


class GalvoMirrorsHW(HardwareComponent):

    name = 'galvo_mirrors'

    def __init__(self, app, debug=False, name=None, axes='xy', min_value=-10, max_value=10, max_step_degree=0.2, rate=1e3):
        self.axes = axes
        self._max_step_degree = max_step_degree
        self._MINVALUE = min_value  # V
        self._MAXVALUE = max_value  # V
        self._RATE = rate  # Hz rate at which waveform is written to outputs

        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        S = self.settings

        pos_lq_kwargs = dict(unit='um', spinbox_decimals=3)
        self.settings.New('x_position', ro=True, **pos_lq_kwargs)
        self.settings.New('y_position', ro=True, **pos_lq_kwargs)
        self.settings.New('x_target_position', **pos_lq_kwargs)
        self.settings.New('y_target_position', **pos_lq_kwargs)

        volt_lq_kwargs = dict(unit='V', spinbox_decimals=6)
        self.settings.New('objective_mag', float, initial=50, unit='X')
        self.settings.New('objective_design_tube_lens_focal_length',
                          float, initial=180, unit='mm',
                          description="Given by the manufacturer. Typically: Nikon and Leica 200 mm, Zeiss 165 mm, Olympus 180 mm. Or equal to EFL*MAGNIFICATION")
        self.settings.New('tube_lens_focal_length',
                          float, initial=200, unit='mm',
                          description="focal length of second lens after the galvo mirror")
        self.settings.New('scan_lens_focal_length',
                          float, initial=50, unit='mm',
                          description="focal length of the lens just after the galvo mirror")
        self.settings.New('volts_per_degree', float, initial=1.0, unit='V/deg')

        for chan, axis in enumerate(self.axes):
            self.settings.New(f'{axis}_output_channel', str, initial=f'Dev1/ao{chan}',
                              description='Physical analog output channel of DAQ')
            self.settings.New(f'{axis}_input_channel', str, initial=f'Dev1/ai{chan}',
                              description='Physical analog input channel, forked of from corresponding analog output. Required to read position')
            offset = self.settings.New(
                f'{axis}_voltage_offset', float, initial=6.1, **volt_lq_kwargs)
            v = self.settings.New(
                f'{axis}_voltage', float, initial=0, **volt_lq_kwargs, ro=True)
            flip = self.settings.New(f'flip_{axis}', bool, initial=False)
            self.settings.New(
                f'{axis}_target_voltage', float, initial=0, **volt_lq_kwargs)
            S.get_lq(f'{axis}_position').connect_lq_math((v, offset, flip), func=self.update_position_from_voltage)

        self.add_operation('update voltage channels',
                           self.update_output_voltages_using_control_ai_channels)

    def connect(self):

        S = self.settings

        for axis in self.axes: 
            S.get_lq(f'{axis}_target_voltage').connect_to_hardware(
                write_func=partial(self.set_target_voltage, axis=axis))
           
            S.get_lq(f'{axis}_target_position').connect_to_hardware(
                write_func=partial(self.move_slow, axis=axis))

        self.update_output_voltages_using_control_ai_channels()

    def get_control_ai(self):
        ''' assuming the output channels are connected to the input channels '''
        S = self.settings
        task = nidaqmx.Task()
        for axis in self.axes:
            task.ai_channels.add_ai_voltage_chan(
                S[f'{axis}_input_channel'], "", min_val=self._MINVALUE, max_val=self._MAXVALUE)

        voltages = task.read()
        task.wait_until_done()
        task.close()
        return voltages

    def update_output_voltages_using_control_ai_channels(self):
        voltages = self.get_control_ai()
        self.settings['x_voltage'] = voltages[0]
        self.settings['y_voltage'] = voltages[1]
        # print(self.name, 'update_output_voltages_using_control_ai_channels', voltages)
        return voltages

    @property
    def effective_mag(self):
        S = self.settings
        return S['objective_mag'] * S['tube_lens_focal_length'] / S['objective_design_tube_lens_focal_length']

    def volts_to_position(self, volts, offset):
        S = self.settings
        volts -= offset
        return S['scan_lens_focal_length'] * 1e3 / self.effective_mag * np.tan(volts / S['volts_per_degree'] * np.pi / 180)

    def position_to_volts(self, position, offset):
        S = self.settings
        return np.arctan(position * self.effective_mag / (S['scan_lens_focal_length'] * 1e3)) * 180 / np.pi * S['volts_per_degree'] + offset

    def disconnect(self):
        pass

    def write_analog_voltages(self, voltages, axis):
        voltages = np.atleast_1d(voltages)
        print(self.name, 'write_analog_voltages', axis, voltages)
        if np.max(voltages) >= self._MAXVALUE or np.min(voltages) <= self._MINVALUE:
            print(self.name, 'attempt to set voltage that breaks galvo??')
            return

        if not self.settings['connected']:
            print(self.name, 'FOR SAFETY: CONNECT FIRST')
            return

        task = nidaqmx.Task()
        S = self.settings
        task.ao_channels.add_ao_voltage_chan(S[f'{axis}_output_channel'],
                                             min_val=self._MINVALUE,
                                             max_val=self._MAXVALUE,
                                             units=VoltageUnits.VOLTS)
        task.timing.cfg_samp_clk_timing(self._RATE,
                                        source="",
                                        active_edge=Edge.RISING,
                                        sample_mode=AcquisitionType.FINITE,
                                        samps_per_chan=len(voltages))
        
        task.write(voltages, auto_start=False, timeout=10.0)
        task.start()
        task.wait_until_done(timeout=10.0)
        # print('wait_until_done DONE')

        task.close()
        self.settings[f'{axis}_voltage'] = voltages[-1]
        if S['debug_mode']:
            print(self.name, 'wrote', voltages, ' voltages to channel', axis)
        self.update_output_voltages_using_control_ai_channels()

    def move_slow_x(self, x_target):
        self.move_slow(x_target, 'x')

    def move_slow_y(self, y_target):
        self.move_slow(y_target, 'y')
        
    def update_position_from_voltage(self, volts, offset, flip):
        if flip:
            volts *= -1
            offset *= -1
        return self.volts_to_position(volts, offset)

    def move_slow(self, target_position, axis):
        fac = -1 if self.settings[f'flip_{axis}'] else 1
        offset = fac * self.settings[f'{axis}_voltage_offset']        
        v_target = fac * self.position_to_volts(target_position, offset)
        self.set_target_voltage(v_target, axis)

    def set_target_voltage(self, v_target, axis):
        self.update_output_voltages_using_control_ai_channels()
        v0 = self.settings[f'{axis}_voltage']
        num = int(np.ceil(np.abs(v0 - v_target) / self.dv))
        voltages = np.linspace(v0, v_target, num + 1)
        self.write_analog_voltages(voltages, axis)

    @property
    def dv(self):
        return self._max_step_degree / self.settings['volts_per_degree']


if __name__ == '__main__':
    Q = GalvoMirrorsHW(3)
    Q.connect()

    # Q.settings['x_target_position'] = -200
    Q.move_slow(-2000, 0)
