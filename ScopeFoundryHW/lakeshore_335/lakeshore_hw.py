from ScopeFoundry import HardwareComponent
# import threading
# import time
from lakeshore.model_335 import *

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

SENSOR_CURVES = ['DT-470 1.4-475K', 'DT-670 1.4-500K', 'DT-500-D 1.4-365K', 'DT-500-E1 1.1-330K',
                 '05 Reserved', 'PT-100 30-800K', 'PT-1000 30-800K', 'RX-102A-AA 0.05-40K',
                 'RX-202A-AA 0.05-40K', '10 Reserved', '11 Reserved', 'Type K 3-1645K',
                 'Type E 3-1274K', 'Type T 3-670K', 'AuFe 0.03% 3.5-500K', 'AuFe 0.07% 3.15-610K']


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
            # self.settings['powerup_enable'] = ans['powerup_enable']
        
    def disconnect(self):
        if hasattr(self, 'face'):
            self.face.disconnect_usb()
            del self.face

        '''
        self.settings.T_A.connect_to_hardware(lambda:self.face.read_T(chan='A'))
        self.settings.T_B.connect_to_hardware(lambda:self.face.read_T(chan='B'))

        S.analog_out_enable.connect_to_hardware(
            read_func=self.face.get_output_enabled,
            write_func=self.face.set_output_enabled)
        
        S.analog_out_channel.connect_to_hardware(
            read_func=self.face.get_output_channel,
            write_func=self.face.set_output_channel)
        
        S.T_at_10V.connect_to_hardware(
            read_func=self.face.get_output_vmax,
            write_func=self.face.set_output_vmax)
        
        S.T_at_0V.connect_to_hardware(
            read_func=self.face.get_output_vmin,
            write_func=self.face.set_output_vmin)
            
        S.setpoint_T.connect_to_hardware(
            read_func=self.face.get_setpoint,
            write_func=self.face.set_setpoint)
        
        S.heater_output.connect_to_hardware(
            read_func=self.face.get_heater_output)
        
        S.heater_range.connect_to_hardware(
            read_func=self.face.get_heater_range,
            write_func=self.face.set_heater_range)
        
        S.control_mode.connect_to_hardware(
            read_func=self.face.get_cmode,
            write_func=self.face.set_cmode)
        
        S.manual_heater_output.connect_to_hardware(
            self.face.get_manual_heater_output,
            self.face.set_manual_heater_output
            )
        
        def set_sensor_A_type(val):
            self.face.set_sensor_type(val, inp='A')

        def get_sensor_A_type():
            return self.face.get_sensor_type(inp='A')

        S.type_A.connect_to_hardware(
            read_func=get_sensor_A_type,
            write_func=set_sensor_A_type)
        
        def set_sensor_A_comp(val):
            self.face.set_sensor_comp(val, inp='A')

        def get_sensor_A_comp():
            return self.face.get_sensor_comp(inp='A')

        S.comp_A.connect_to_hardware(
            read_func=get_sensor_A_comp,
            write_func=set_sensor_A_comp)
        
        def set_sensor_A_curve(val):
            self.face.set_input_curve(val, inp='A')

        def get_sensor_A_curve():
            return self.face.get_input_curve(inp='A')

        S.curve_A.connect_to_hardware(
            read_func=get_sensor_A_curve,
            write_func=set_sensor_A_curve)        
                
        def set_sensor_B_type(val):
            self.face.set_sensor_type(val, inp='B')

        def get_sensor_B_type():
            return self.face.get_sensor_type(inp='B')

        S.type_B.connect_to_hardware(
            read_func=get_sensor_B_type,
            write_func=set_sensor_B_type)
        
        def set_sensor_B_comp(val):
            self.face.set_sensor_comp(val, inp='B')

        def get_sensor_B_comp():
            return self.face.get_sensor_comp(inp='B')

        S.comp_B.connect_to_hardware(
            read_func=get_sensor_B_comp,
            write_func=set_sensor_B_comp)

        def set_sensor_B_curve(val):
            self.face.set_input_curve(val, inp='B')

        def get_sensor_B_curve():
            return self.face.get_input_curve(inp='B')

        S.curve_B.connect_to_hardware(
            read_func=get_sensor_B_curve,
            write_func=set_sensor_B_curve)

        # Note only loop 1 (out of 2 possible loops) is used. 
        S.K_P1.connect_to_hardware(
            read_func=lambda:self.get_P(1),
            write_func=lambda x:self.write_PID(1))
        S.K_I1.connect_to_hardware(
            read_func=lambda: self.get_I(1),
            write_func=lambda x:self.write_PID(1))     
        S.K_D1.connect_to_hardware(
            read_func=lambda: self.get_D(1),
            write_func=lambda x:self.write_PID(1))
        
        S.ramp_on.connect_to_hardware(
            read_func=lambda:self.face.get_ramp_onoff(1),
            write_func=lambda x:self.face.set_ramp_params(x, self.settings['ramp_rate'], 1)
            )
        S.ramp_rate.connect_to_hardware(
            read_func=lambda:self.face.get_ramp_rate(1),
            write_func=lambda x:self.face.set_ramp_params(self.settings['ramp_on'], x, 1)
            )        
        S.is_ramping.connect_to_hardware(lambda:self.face.is_ramping(1))
        S.is_tunning.connect_to_hardware(self.face.get_tune_status)     
        S.control_input.connect_to_hardware(
            read_func=lambda: self.face.get_cset(1)[0],
            write_func=lambda x:self.face.set_cset(1, x),
            )

        self.read_from_hardware()
        
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)
        time.sleep(0.2)
        self.update_thread.start()
        
        
    def get_P(self, loop):
        return self.face.get_PID(loop)[0]

    def get_I(self, loop):
        return self.face.get_PID(loop)[1]

    def get_D(self, loop):
        return self.face.get_PID(loop)[2]
    
    def write_PID(self, loop):
        S = self.settings
        l = loop
        self.face.set_PID(l, S[f'K_P{l}'], S[f'K_I{l}'], S[f'K_D{l}'])    
        
    def disconnect(self):
        
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread
    
        if hasattr(self, 'face'):
            self.face.set_heater_range('off')
            self.face.set_cmode('Manual PID')
            self.face.set_output_enabled(False)        
            self.face.ask('*CLS')
            self.face.close()
            del self.face
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            self.settings.T_A.read_from_hardware()
            self.settings.T_B.read_from_hardware()
            self.settings.heater_output.read_from_hardware()
            self.settings.is_ramping.read_from_hardware()
            self.settings.is_tunning.read_from_hardware()
            P1, I1, D1 = self.face.get_PID(1)
            self.settings.K_P1.update_value(P1)
            self.settings.K_I1.update_value(I1)
            self.settings.K_D1.update_value(D1)
            time.sleep(1.0)
    '''
