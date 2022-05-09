from ScopeFoundry import HardwareComponent
import numpy as np

import nidaqmx
from nidaqmx.constants import VoltageUnits, AcquisitionType, Edge
from nidaqmx._lib import lib_importer
from nidaqmx.errors import check_for_error


def clear_task_with_handle(task_handle: int):
    cfunc = lib_importer.windll.DAQmxClearTask
    if cfunc.argtypes is None:
        with cfunc.arglock:
            if cfunc.argtypes is None:
                cfunc.argtypes = [
                    lib_importer.task_handle]

    error_code = cfunc(
        task_handle)
    check_for_error(error_code)

    task_handle = None


def clear_task_callback(task_handle, status, callback_data):
    print('clear_task_callback')
    clear_task_with_handle(task_handle)
    return 0


class GalvoMirrorsHW(HardwareComponent):

    name = 'galvo_mirrors'

    def __init__(self, app, debug=False, name=None, axes='xy', channels=(0, 1), min_value=-10, max_value=10, max_step_degree=0.2, rate=1e3):
        self.chan2axis = {c: a for c, a in zip(channels, axes)}
        self.axis2chan = {v: k for k, v in self.chan2axis.items()}

        self._max_step_degree = max_step_degree
        self._MINVALUE = min_value  # V
        self._MAXVALUE = max_value  # V
        self._RATE = rate  # Hz rate at witch waveform is written to outputs

        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        S = self.settings

        pos_lq_kwargs = dict(unit='um', spinbox_decimals=3)
        self.settings.New('x_position', ro=True, **pos_lq_kwargs)
        self.settings.New('y_position', ro=True, **pos_lq_kwargs)
        self.settings.New('x_target_position', **pos_lq_kwargs)
        self.settings.New('y_target_position', **pos_lq_kwargs)

        volt_lq_kwargs = dict(unit='V', spinbox_decimals=3)
        self.settings.New('objective_mag', float, initial=50, unit='X')
        self.settings.New('objective_focal_length',
                          float, initial=180, unit='mm')
        self.settings.New('tube_lens_focal_length',
                          float, initial=200, unit='mm')
        self.settings.New('scan_lens_focal_length',
                          float, initial=50, unit='mm')
        self.settings.New('volts_per_degree', float, initial=1.0, unit='V/deg')

        for chan, axis in self.chan2axis.items():
            self.settings.New(f'channel_{chan}', str, initial=f'Dev1/ao{chan}')
            self.settings.New(f'control_ai_channel_{chan}', str, initial=f'Dev1/ai{chan}',
                              description='connect this to the corresponding analog output, allows to know positions at startup')
            offset = self.settings.New(
                f'voltage_offset_{chan}', float, initial=6.1, **volt_lq_kwargs)
            v = self.settings.New(
                f'voltage_{chan}', float, initial=0, **volt_lq_kwargs, ro=True)
            self.settings.New(
                f'voltage_target_{chan}', float, initial=0, **volt_lq_kwargs)
            S.get_lq(f'{axis}_position').connect_lq_math((v, offset),
                                                         func=self.volts_to_position)

        self.add_operation('update voltage channels',
                           self.update_output_voltages_using_control_ai_channels)

    def connect(self):

        S = self.settings

        self.settings.get_lq(f'voltage_target_0').connect_to_hardware(
            write_func=lambda value: self.set_target_voltage(value, channel=0)
        )
        self.settings.get_lq(f'voltage_target_1').connect_to_hardware(
            write_func=lambda value: self.set_target_voltage(value, channel=1)
        )

        S.x_target_position.connect_to_hardware(
            write_func=self.move_slow_x,
        )
        S.y_target_position.connect_to_hardware(
            write_func=self.move_slow_y,
        )

        self.update_output_voltages_using_control_ai_channels()

    def get_control_ai(self):
        ''' assuming the output channels are connected to the input channels '''
        S = self.settings
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(
            S['control_ai_channel_0'], "", min_val=self._MINVALUE, max_val=self._MAXVALUE)
        task.ai_channels.add_ai_voltage_chan(
            S['control_ai_channel_1'], "", min_val=self._MINVALUE, max_val=self._MAXVALUE)
        voltages = task.read()
        task.wait_until_done()
        task.close()
        return voltages

    def update_output_voltages_using_control_ai_channels(self):
        voltages = self.get_control_ai()
        self.settings['voltage_0'] = voltages[0]
        self.settings['voltage_1'] = voltages[1]
        #print(self.name, 'update_output_voltages_using_control_ai_channels', voltages)
        return voltages

    @property
    def effective_mag(self):
        S = self.settings
        return S['objective_mag'] * S['tube_lens_focal_length'] / S['objective_focal_length']

    def volts_to_position(self, volts, offset):
        S = self.settings
        volts -= offset
        return S['scan_lens_focal_length'] * 1e3 / self.effective_mag * np.tan(volts / S['volts_per_degree'] * np.pi / 180)

    def position_to_volts(self, position):
        S = self.settings
        return np.arctan(position * self.effective_mag / (S['scan_lens_focal_length'] * 1e3)) * 180 / np.pi * S['volts_per_degree']

    def disconnect(self):
        pass

    def write_analog_voltages(self, voltages, channel=0):
        voltages = np.atleast_1d(voltages)
        print(self.name, 'write_analog_voltages', voltages)
        if np.max(voltages) >= self._MAXVALUE or np.min(voltages) <= self._MINVALUE:
            print(self.name, 'attempt to set voltage that breaks galvo??')
            return

        if not self.settings['connected']:
            print(self.name, 'FOR SAFETY: CONNECT FIRST')
            return

        task = nidaqmx.Task()
        S = self.settings
        task.ao_channels.add_ao_voltage_chan(S[f'channel_{channel}'],
                                             min_val=self._MINVALUE,
                                             max_val=self._MAXVALUE,
                                             units=VoltageUnits.VOLTS)
        task.timing.cfg_samp_clk_timing(self._RATE,
                                        source="",
                                        active_edge=Edge.RISING,
                                        sample_mode=AcquisitionType.FINITE,
                                        samps_per_chan=len(voltages))
        # task.register_done_event(clear_task_callback)

        task.write(voltages, auto_start=False, timeout=10.0)
        task.start()
        task.wait_until_done(timeout=10.0)
        # print('wait_until_done DONE')

        task.close()
        self.settings[f'voltage_{channel}'] = voltages[-1]
        print(self.name, 'wrote', voltages, ' voltages to channel', channel)
        self.update_output_voltages_using_control_ai_channels()

    def move_slow_xy(self, x_target, y_target):
        S = self.settings
        v_target_x = self.position_to_volts(
            x_target) + S[f"voltage_offset_{self.axis2chan['x']}"]
        v_target_y = self.position_to_volts(
            y_target) + S[f"voltage_offset_{self.axis2chan['y']}"]

        v_0_x = S[f"voltage_{self.axis2chan['x']}"]
        v_0_y = S[f"voltage_{self.axis2chan['y']}"]

        Nx = (v_target_x - v_0_x) / self.dv
        Ny = (v_target_y - v_0_y) / self.dv
        N = max((Nx, Ny))

        voltages_x = np.linspace(v_0_x, v_target_x, N)
        voltages_y = np.linspace(v_0_y, v_target_y, N)

    def move_slow_x(self, x_target):
        self.move_slow(x_target, self.axis2chan['x'])

    def move_slow_y(self, y_target):
        self.move_slow(y_target, self.axis2chan['y'])

    def move_slow(self, target_position, channel):
        v_target = self.position_to_volts(
            target_position) + self.settings[f'voltage_offset_{channel}']
        self.set_target_voltage(v_target, channel)

    def set_target_voltage(self, v_target, channel):
        self.update_output_voltages_using_control_ai_channels()
        v0 = self.settings[f'voltage_{channel}']
        num = int(np.ceil(np.abs(v0 - v_target) / self.dv))
        voltages = np.linspace(v0, v_target, num + 1)
        self.write_analog_voltages(voltages, channel)

    @property
    def dv(self):
        return self._max_step_degree / self.settings['volts_per_degree']


if __name__ == '__main__':
    Q = GalvoMirrorsHW(3)
    Q.connect()

    # Q.settings['x_target_position'] = -200
    Q.move_slow(-2000, 0)
