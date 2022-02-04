from ScopeFoundry import HardwareComponent
import threading
import time

try: 
    from .lakeshore_interface import Lakeshore331Interface, HEATER_RANGE_CHOICES, SENSOR_TYPES, CONTROL_MODES, SENSOR_CURVES
except Exception as ex:
    print("Cannot load required module for Lakeshore 331 T Controller", ex)
    

class Lakeshore331HW(HardwareComponent):
    
    name = 'lakeshore331'
    
    def __init__(self, app, name=None, debug=False, port='COM6'):
        self.port = port
        HardwareComponent.__init__(self, app, debug=debug, name=name)
        
    def setup(self):
        S = self.settings
        S.New('port', ro=False, initial=self.port, dtype=str)
        
        # Temperature readings
        S.New('T_A', ro=True, initial=0.0, unit='K')
        S.New('T_B', ro=True, initial=0.0, unit='K')
        
        # Analog out settings
        S.New('analog_out_enable', ro=False, initial=False, dtype=bool)
        S.New('analog_out_channel', ro=False, initial='B', dtype=str, choices=['A', 'B'])
        S.New('T_at_10V', ro=False, initial=1000.0, dtype=float, unit='K')
        S.New('T_at_0V', ro=False, initial=0.0, dtype=float, unit='K')
        
        # T control settings
        # Note only loop 1 (out of 2 possible loops) is used
        S.New('setpoint_T', ro=False, initial=20.0, dtype=float, unit='K',
              description='specifies setpoint temperature for loop 1. Use control input to specify which temperature to control from')
        S.New('control_input', initial='A', dtype=str, choices=('A', 'B'),
              description='Specifies which temperature to control from.')
        S.New('K_P1', ro=False, dtype=float, initial=50.0)
        S.New('K_I1', ro=False, dtype=float, initial=0.0)
        S.New('K_D1', ro=False, dtype=float, initial=0.0)
        S.New('heater_output', ro=False, dtype=float, unit='%', description='current power output of the heater')
        S.New('heater_range', ro=False, dtype=str, initial=HEATER_RANGE_CHOICES[0], choices=HEATER_RANGE_CHOICES,
              description='set to <b>off</b> to turn heater off')
        S.New('control_mode', ro=False, dtype=str, initial=CONTROL_MODES[0], choices=CONTROL_MODES)
        S.New('ramp_on', ro=False, dtype=bool, initial=False)
        S.New('ramp_rate', ro=False, dtype=float, initial=10.0)
        S.New('is_ramping', ro=True, dtype=bool, initial=False)
        S.New('is_tunning', ro=True, dtype=bool, initial=False)
        S.New('manual_heater_output', float, initial=0, unit='%',
              description='set <b>control_mode</b> to <i>Open Loop</i> to use.')
                
        # Sensor settings
        S.New('type_A', ro=False, dtype=str, choices=SENSOR_TYPES)
        S.New('comp_A', ro=False, dtype=bool, initial=False)
        S.New('curve_A', ro=False, dtype=str, choices=SENSOR_CURVES)
        S.New('type_B', ro=False, dtype=str, choices=SENSOR_TYPES)
        S.New('comp_B', ro=False, dtype=bool, initial=False)
        S.New('curve_B', ro=False, dtype=str, choices=SENSOR_CURVES)
        
        self.add_operation("Reset", self.reset)
    
    def reset(self):
        self.face.reset()
    
    def connect(self):
        S = self.settings
        self.face = Lakeshore331Interface(debug=S['debug_mode'], port=S['port'])
        print(self.face.info())
        resp_dict = self.face.get_output()

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
