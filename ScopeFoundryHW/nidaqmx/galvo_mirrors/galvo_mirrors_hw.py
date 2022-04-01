from ScopeFoundry import HardwareComponent
# import PyDAQmx
import numpy as np
# from PyDAQmx import Task

import nidaqmx


class GalvoMirrorsHW(HardwareComponent):
    
    name = 'galvo_mirrors'
    
    def __init__(self, app, debug=False, name=None, axes='xy', dVdt_max=0.65 / 130e-3, min_value=-10, max_value=10, rate=1e5):
        self.dVdt_max = dVdt_max  # V/sec
        self.channels = (0, 1)
        self.chan2axis = {}
        for c, a in zip(self.channels, axes):
            self.chan2axis[c] = a
        self.axis2chan = {v: k for k, v in self.chan2axis.items()}

        self._MINVALUE = min_value  # V
        self._MAXVALUE = max_value  # V
        self._RATE = rate  # Hz rate at witch waveform is written to outputs
        
        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        S = self.settings

        self.settings.New('x_position', unit='um')
        self.settings.New('y_position', unit='um')

        self.settings.New('x_target_position', unit='um')
        self.settings.New('y_target_position', unit='um')
        self.settings.New('volts_per_degree', float, initial=1.0, ro=True, unit='V/deg')

        self.settings.New('objective_mag', float, initial=50, unit='X')
        self.settings.New('objective_focal_length', float, initial=180, unit='mm')
        self.settings.New('tube_lens_focal_length', float, initial=200, unit='mm')
        self.settings.New('scan_lens_focal_length', float, initial=50, unit='mm')

        for chan, axis in self.chan2axis.items():
            self.settings.New(f'channel_{chan}', str, initial=f'Dev1/ao{chan}')
            self.settings.New(f'voltage_offset_{chan}', float, initial=6.1, unit='V')
            v = self.settings.New(f'voltage_{chan}', float, initial=0, unit='V')           
            S.get_lq(f'{axis}_position').connect_lq_math(v,
                              func=self.volts_to_position)
        
    @property
    def effective_mag(self):
        S = self.settings
        return S['objective_mag'] * S['tube_lens_focal_length'] / S['objective_focal_length']
            
    def volts_to_position(self, volts):
        S = self.settings
        return S['scan_lens_focal_length'] * 1e3 * np.tan(volts / S['volts_per_degree'] * np.pi / 180) * self.effective_mag
    
    def position_to_volts(self, position):
        S = self.settings
        return np.arctan(position * self.effective_mag / (S['scan_lens_focal_length'] * 1e3)) * 180 / np.pi * S['volts_per_degree']
    
    def connect(self):
        
        S = self.settings
        
        self.tasks = []
        
        for chan in self.channels:
            
            # task = Task()
            # task.CreateAOVoltageChan(S[f'channel_{i}'], "", -10.0, 10.0, PyDAQmx.DAQmx_Val_Volts, None)
            # task.set_rate(self.rate)
            # task.StartTask()
            # self.tasks.append(task)
            
            task = nidaqmx.Task()
            
            c = task.ao_channels.add_ao_voltage_chan(S[f'channel_{chan}'],
                                                 min_val=self._MINVALUE,
                                                 max_val=self._MAXVALUE,
                                                 units=nidaqmx.constants.VoltageUnits.VOLTS)
            task.timing.cfg_samp_clk_timing(self._RATE)
            
            task.start()
            self.tasks.append(task)
            
        self.settings.get_lq(f'voltage_0').connect_to_hardware(
            write_func=lambda value:self.write_analog_voltage(value, channel=0)
            )
        self.settings.get_lq(f'voltage_1').connect_to_hardware(
            write_func=lambda value:self.write_analog_voltage(value, channel=1)
            )        
        
        S.x_target_position.connect_to_hardware(
            write_func=self.move_slow_x,
            )
        S.y_target_position.connect_to_hardware(
            write_func=self.move_slow_y,
            )
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'tasks'):
            for task in self.tasks: 
                task.StopTask()
            del self.tasks
        
    def write_analog_voltage(self, voltages, channel=0):
        if voltages >= self._MAXVALUE or voltages <= self._MINVALUE:
            print(self.name, 'attempt to set voltage that breaks galvo??')
            return
        task = self.tasks[channel]
        task.write(voltages)
        print(self.name, 'wrote', voltages, 'to channel', channel)
        # task = self.tasks[channel]
        # task.WriteAnalogScalarF64(1, 10.0, value, None)
        
    def move_slow_x(self, x_target):
        self.move_slow(x_target, self.axis2chan['x'])
        
    def move_slow_y(self, y_target):
        self.move_slow(y_target, self.axis2chan['y'])
    
    def move_slow(self, target_position, channel):
        v_target = self.position_to_volts(target_position) + self.settings[f'voltage_offset_{channel}']
        v0 = self.settings[f'voltage_{channel}']
        dv = self.dVdt_max / self.rate
        num = int(np.ceil(np.abs(v0 - v_target)) / dv)
        
        voltages = np.linspace(v0 + dv, v_target, num - 1)
        
        print(target_position, (voltages))
        self.write_analog_voltage(voltages, channel)
        
    def _write_voltages(self, voltages, channel):
        '''retired??'''
        
        if np.abs(voltages).max() >= 10:
            print(self.name, 'attempt to set voltage that breaks galvo??')
        task = self.tasks[channel]
        if len(voltages) > 1:
            # task.
            # task.WriteAnalogF64(1, PyDAQmx.bool32(0), 1.0,
            #                PyDAQmx.DAQmx_Val_GroupByChannel, voltages, PyDAQmx.byref(PyDAQmx.int32()), None)
            self.settings[f'voltage_{channel}'] = voltages[-1]
        else:
            self.settings[f'voltage_{channel}'] = voltages
        
        
if __name__ == '__main__':
    Q = NIDAQGalvoMirrorControl(3)
    
    # Q.settings['x_target_position'] = -200
    Q.move_slow(-2000, 0)
        
