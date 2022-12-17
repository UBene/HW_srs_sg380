'''
Created on Jan 15, 2022

@author: Benedikt Ursprung

requires: pip install lakeshore
'''

from ScopeFoundry import HardwareComponent
from lakeshore.model_335 import Model335HeaterRange, Model335HeaterOutputMode, \
    Model335InputSensor, Model335InputSensorType, Model335InputSensorUnits, \
    Model335DiodeRange, Model335RTDRange, Model335ThermocoupleRange, \
    Model335InputSensorSettings, Model335

WAIT_TIME = 0.1
HEATER_RANGE_CHOICES = [(a.name, a.value) for a in Model335HeaterRange]
HEATER_OUTPUT_MODE_CHOICES = [(a.name, a.value) for a in Model335HeaterOutputMode]
INPUT_SENSOR_CHOICES = [(a.name, a.value) for a in Model335InputSensor]
SENSOR_TYPES_CHOICES = [(a.name, a.value) for a in Model335InputSensorType]
INPUT_SENSOR_UNITS_CHOICES = [(a.name, a.value) for a in Model335InputSensorUnits]
INPUT_RANGES_CHOICES = []
for t in [Model335DiodeRange, Model335RTDRange, Model335ThermocoupleRange]:
    for a in t:
        INPUT_RANGES_CHOICES.append((a.name, a.value))


class Lakeshore335HW(HardwareComponent):
    
    name = 'lakeshore335'
    
    def __init__(self, app, name=None, debug=False, port='COM6'):
        self.port = port
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    def setup(self):
        S = self.settings
        S.New('baud_rate', int, initial=57600)
        
        # Temperature readings
        S.New('T_A', ro=True, initial=0.0, unit='K')
        S.New('T_B', ro=True, initial=0.0, unit='K')
                
        # T control settings
        # Note only loop 1 (out of 2 possible loops) is used
        S.New('setpoint_T', float, ro=False, initial=20.0, unit='K',
              description='specifies setpoint temperature for loop 1. Use control input to specify which temperature to control from')
        S.New('input_sensor', initial=INPUT_SENSOR_CHOICES[0][1], dtype=str,
              choices=INPUT_SENSOR_CHOICES,
              description='Specifies which temperature to control from.')
        
        S.New('gain', ro=False, dtype=float, initial=50.0)
        S.New('integral', ro=False, dtype=float, initial=0.0)
        S.New('derivative', ro=False, dtype=float, initial=0.0)
        
        S.New('heater_output', ro=False, dtype=float, unit='%', description='current power output of the heater')
        S.New('heater_range', ro=False, dtype=str, choices=HEATER_RANGE_CHOICES,
              description='set to <b>off</b> to turn heater off')
        S.New('heater_output_mode', ro=False, dtype=str,
              initial=HEATER_OUTPUT_MODE_CHOICES[0][1],
              choices=HEATER_OUTPUT_MODE_CHOICES)
        
        S.New('ramp_enable', ro=False, dtype=bool, initial=False)
        S.New('rate_value', ro=False, dtype=float, initial=10.0,
              description='of ramp', unit='K/sec?', vmin=0.1, vmax=100)
        S.New('ramp_status', ro=True, dtype=bool, initial=False)
        S.New('manual_heater_output', float, initial=0, unit='%',
              description='set <b>heater_output_mode</b> to <i>CLOSED_LOOP</i> to use.',
              vmin=0, vmax=100)
        S.New('analog_output', float, initial=0, unit='%',
              description='current heater output')
                
        # Sensor settings
        for channel in ('A', 'B'):
            S.New(f'sensor_type_{channel}', str, initial=SENSOR_TYPES_CHOICES[1][1],
                  choices=SENSOR_TYPES_CHOICES)
            S.New(f'autorange_enable_{channel}', bool, initial=False)
            S.New(f'compensation_{channel}', bool, initial=False)
            S.New(f'units_{channel}', int, initial=INPUT_SENSOR_UNITS_CHOICES[0][1],
                  choices=INPUT_SENSOR_UNITS_CHOICES)
            S.New(f'input_range_{channel}', int, choices=INPUT_RANGES_CHOICES)
        
        S.input_sensor.connect_to_hardware(self.set_heater_output_mode)
        S.heater_output_mode.add_listener(self.set_heater_output_mode)
        
        self.add_operation("write sensor A", lambda:self.set_sensor('A'))
        self.add_operation("write sensor B", lambda:self.set_sensor('B'))
        self.add_operation("update sensor A", lambda:self.update_sensor('A'))
        self.add_operation("update sensor B", lambda:self.update_sensor('B'))
        self.add_operation("update output mode", self.get_heater_output_mode)
    
    def set_sensor(self, channel):
        if hasattr(self, 'face'):
            self.face.set_input_sensor(channel,
                Model335InputSensorSettings(
                    self.settings[f'sensor_type_{channel}'],
                    self.settings[f'autorange_enable_{channel}'],
                    self.settings[f'compensation_{channel}'],
                    self.settings[f'units_{channel}'],
                    self.settings[f'input_range_{channel}'],
                    ))
        
    def update_sensor(self, channel):
        if hasattr(self, 'face'):
            ans = self.face.get_input_sensor(channel).__dict__
            if self.settings['debug_mode']:print(self.name, channel, ans)
            self.settings[f'sensor_type_{channel}'] = ans['sensor_type'].value
            self.settings[f'autorange_enable_{channel}'] = ans['autorange_enable']
            self.settings[f'compensation_{channel}'] = ans['compensation']
            self.settings[f'units_{channel}'] = ans['units'].value
            self.settings[f'input_range_{channel}'] = ans['units']
            
    def reset(self):
        self.face.reset()
    
    def connect(self):
        
        S = self.settings
        self.face = dev = Model335(S['baud_rate'])

        S.T_A.connect_to_hardware(lambda:dev.get_kelvin_reading(1))
        S.T_B.connect_to_hardware(lambda:dev.get_kelvin_reading(2))
        
        S.setpoint_T.connect_to_hardware(
            lambda:dev.get_control_setpoint(1),
            lambda value:dev.set_control_setpoint(1, value))
        
        S.manual_heater_output.connect_to_hardware(
            lambda:dev.get_manual_output(1),
            lambda value:dev.set_manual_output(1, value))
        
        S.gain.connect_to_hardware(
            lambda: dev.get_heater_pid(1)['gain'],
            lambda gain:dev.set_heater_pid(1, gain, S['integral'], S['derivative']))
        S.integral.connect_to_hardware(
            lambda: dev.get_heater_pid(1)['integral'],
            lambda integral:dev.set_heater_pid(1, S['gain'], integral, S['derivative']))
        S.gain.connect_to_hardware(
            lambda: dev.get_heater_pid(1)['derivatives'],
            lambda derivative:dev.set_heater_pid(1, S['gain'], S['integral'], derivative))
        
        S.heater_output.connect_to_hardware(lambda:dev.get_heater_output(1))
        
        S.heater_range.connect_to_hardware(
            lambda: dev.get_heater_range(1),
            lambda heater_range: dev.set_heater_range(1, heater_range)
            )
        
        S.ramp_enable.connect_to_hardware(
            lambda: dev.get_setpoint_ramp_parameter(1)['ramp_enable'],
            lambda ramp_enable: dev.set_setpoint_ramp_parameter(1, ramp_enable, S['rate_value'])
            )
        S.rate_value.connect_to_hardware(
            lambda: dev.get_setpoint_ramp_parameter(1)['rate_value'],
            lambda rate_value: dev.set_setpoint_ramp_parameter(1, S['ramp_enable'], rate_value)
            )
        
        S.ramp_status.connect_to_hardware(lambda: dev.get_setpoint_ramp_status(1))
        
        self.update_sensor('A')
        self.update_sensor('B')

    def set_heater_output_mode(self, output=1):
        if hasattr(self, 'face'):
            print(self.settings['heater_output_mode'], self.settings['input_sensor'])
            self.face.set_heater_output_mode(output,
                                             self.settings['heater_output_mode'],
                                             self.settings['input_sensor'])        
        
    def get_heater_output_mode(self, output=1):
        if hasattr(self, 'face'):
            ans = self.face.get_heater_output_mode(output)
            self.settings['heater_output_mode'] = ans['mode'].value
            self.settings['input_sensor'] = ans['channel'].value
        
    def disconnect(self):
        if hasattr(self, 'face'):
            self.face.disconnect_usb()
            del self.face

