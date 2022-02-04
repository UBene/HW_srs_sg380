import serial
import threading
import binascii
from collections import OrderedDict
import time

WAIT_TIME = 0.1
HEATER_RANGE_CHOICES = ['off', 'low (0.5W)', 'med (5W)', 'high (50W)']
SENSOR_TYPES = ['Si diode', 'GaAlAs diode', '100 Ohm Pt/250', '100 Ohm Pt/500', '100 Ohm Pt',
               'NTC RTD', 'TC 25mV', 'TC 50 mV', '2.5V, 1mA', '7.5V, 1mA']
CONTROL_MODES = ['Manual PID', 'Zone', 'Open Loop', 'AutoTune PID', 'AutoTune PI', 'AutoTune P']
SENSOR_CURVES = ['DT-470 1.4-475K', 'DT-670 1.4-500K', 'DT-500-D 1.4-365K', 'DT-500-E1 1.1-330K',
                 '05 Reserved', 'PT-100 30-800K', 'PT-1000 30-800K', 'RX-102A-AA 0.05-40K',
                 'RX-202A-AA 0.05-40K', '10 Reserved', '11 Reserved', 'Type K 3-1645K',
                 'Type E 3-1274K', 'Type T 3-670K', 'AuFe 0.03% 3.5-500K', 'AuFe 0.07% 3.15-610K']


def replace_letters(inputstr):
    # output from Lakeshore is offset in hex by a value of ord('a') - 2 
    # this returns the corrected hex digit
    return str(ord(inputstr) - ord('a') + 2)

        
def decode_garbage(garbagein):
    # output from Lakeshore is off by a weird amount. Everything that isn't ASCII
    # is offset in one of its hex digits by ord('a') - 2. This function fixes this by
    # converting to hex and processing the hex representation of each character
    # before returning the corrected string representation
    hline = garbagein.hex()
    # print(hline)
    hline_arr = [hline[i:i + 2] for i in range(0, len(hline), 2)]
    asdf = ''
    for kk in hline_arr:
        try: 
            if kk == '0d':
                continue
            this_char = binascii.unhexlify(kk)
            asdf = asdf + this_char.decode('ASCII')
        except Exception as ex:
            # print('not an ascii character')
            if kk == '8a':
                continue
            if kk[0] >= 'a': 
                # print(replace_letters(kk[0]))
                kk = replace_letters(kk[0]) + kk[1]
            else:
                # print(replace_letters(kk[1]))
                kk = kk[0] + replace_letters(kk[1])
            this_char = binascii.unhexlify(kk)
            asdf = asdf + this_char.decode('ASCII')
    return asdf


class Lakeshore331Interface(object):
    
    def __init__(self, port='COM21', debug=False):
        self.port = port
        self.debug = debug
        self.lock = threading.Lock()
        self.ser = serial.Serial(port=self.port,
                        baudrate=9600,
                        timeout=1,
                        bytesize=7,
                        parity=serial.PARITY_ODD,
                        stopbits=1, xonxoff=0, rtscts=0)
        # self.ask('*RST')
        self.ask('*CLS')
    
    def info(self):
        resp = self.ask("*IDN?")
        if self.debug: print("Lakeshore 331 Info", resp)
        return resp
    
    def close(self):
        self.ser.close()
    
    def send_cmd(self, cmd):
        self.ser.flush()
        cmd_bytes = (cmd + '\r\n').encode()
        if self.debug: print("Lakeshore 331 cmd: ", repr(cmd), repr(cmd_bytes))
        self.ser.write(cmd_bytes)
        time.sleep(WAIT_TIME)
        if self.debug: print("Lakeshore 331 done sending cmd")    
    
    def read_resp(self):
        self.ser.flush()
        resp = self.ser.readline()
        time.sleep(WAIT_TIME)
        if self.debug: print("Lakeshore 331 resp: ", repr(resp))
        return str(resp, 'ASCII')
    
    def read_T(self, chan='B'):
        resp = self.ask("KRDG? " + chan)
        if resp == '':
            return -1.0
        return float(resp)
        
    def set_output_enabled(self, enable):
        assert isinstance(enable, bool)
        out_dict = self.get_output()
        self.set_output(enable=int(enable == True),
                        chan=out_dict['channel'],
                        vmax=out_dict['max_10V'],
                        vmin=out_dict['min_0V'])
        
    def get_output_enabled(self):
        out_dict = self.get_output()
        return bool(out_dict['enable'])
    
    def set_output_channel(self, chan):
        assert chan == 'A' or chan == 'B'
        out_dict = self.get_output()
        self.set_output(enable=out_dict['enable'],
                        chan=chan,
                        vmax=out_dict['max_10V'],
                        vmin=out_dict['min_0V'])
    
    def get_output_channel(self):
        out_dict = self.get_output()
        return out_dict['channel']
    
    def set_output_vmax(self, vmax):
        out_dict = self.get_output()
        assert vmax > out_dict['min_0V'] and isinstance(vmax, float)
        self.set_output(enable=out_dict['enable'],
                        chan=out_dict['channel'],
                        vmin=out_dict['min_0V'],
                        vmax=vmax)
        
    def get_output_vmax(self):
        return self.get_output()['max_10V']
    
    def set_output_vmin(self, vmin):
        out_dict = self.get_output()
        assert vmin < out_dict['max_10V'] and vmin > 0 and isinstance(vmin, float)
        self.set_output(enable=out_dict['enable'],
                        chan=out_dict['channel'],
                        vmax=out_dict['max_10V'],
                        vmin=vmin)
        
    def get_output_vmin(self):
        return self.get_output()['min_0V']
        
    def set_output(self, enable=1, chan='A', vmax=100.0, vmin=0.0):
        self.ask('ANALOG 0,%d,%s,1,+%0.1f,+%0.1f,+0.0' % (enable, chan, vmax, vmin))
            
    def get_output(self):
        resp = self.ask('ANALOG?')
        if self.debug: print(resp)
        if resp == '':
            raise Exception('Error - no output in', resp)
            return None
        else:
            resp = resp.split(sep=',')
            resp_dict = OrderedDict(
                [('bipolar', int(resp[0])),
                ('enable', int(resp[1])),
                ('channel', resp[2]),
                ('max_10V', float(resp[4])),
                ('min_0V', float(resp[5])),
                ('manual', float(resp[6])), ])
            if self.debug: 
                print("Lakeshore 331 analog output setup: ")
                for key, value in resp_dict.items():
                    print(key + ' ' + str(value))
            
            return resp_dict 
    
    def ask(self, cmd):
        with self.lock:
            self.send_cmd(cmd)
            return self.read_resp()
    
    def set_heater_range(self, val):
        assert val in HEATER_RANGE_CHOICES
        ind = HEATER_RANGE_CHOICES.index(val)
        self.ask('RANGE %d' % ind)
        if self.debug: print('Lakeshore 331 heater range set to %d sent' % ind)
        
    def get_remote_mode(self):
        return self.ask('MODE?')
    
    def set_remote_mode(self, ind):
        assert isinstance(ind, int) and ind >= 0 and ind <= 2
        self.ask('MODE %d' % ind)
        if self.debug: print('Lakeshore 331 remote mode set to %d sent' % ind)
        
    def get_input_type(self, inp='B'):
        assert inp in ['A', 'B']
        resp = self.ask('INTYPE? %s' % inp)
        if self.debug: print('Lakeshore 331 input %s type %s' % (inp, resp))
        [ind, comp] = resp.split(sep=',')
        return [int(ind), int(comp)]
    
    def get_sensor_type(self, inp='B'):
        ind, comp = self.get_input_type(inp=inp)
        return SENSOR_TYPES[ind]
    
    def get_sensor_comp(self, inp='B'):
        ind, comp = self.get_input_type(inp=inp)
        return bool(comp)
    
    def set_sensor_type(self, val, inp='B',):
        ind, comp = self.get_input_type(inp=inp)
        self.ask('INTYPE %s, %d, %d' % (inp, SENSOR_TYPES.index(val), comp))
        
    def set_sensor_comp(self, val, inp='B'):
        assert isinstance(val, bool)
        ind, comp = self.get_input_type(inp=inp)
        self.ask('INTYPE %s, %d, %d' % (inp, ind, int(val)))
    
    def set_manual_heater_output(self, pwr, loop=1):
        resp = self.ask(f'MOUT {loop},{pwr}')
        if self.debug:print('Lakeshore 331 set_manual_heater_output', repr(resp))
        
    def get_manual_heater_output(self, loop=1):
        resp = self.ask('MOUT? {loop}')
        if self.debug:print('Lakeshore 331 get_manual_heater_output', repr(resp))
        return float(resp)
    
    def get_heater_output(self):
        resp = self.ask('HTR?')
        if self.debug: print('Lakeshore 331 heater output at %s' % resp)
        return float(resp)
    
    def get_heater_status(self):
        resp = self.ask('HTRST?')
        if self.debug: print('Lakeshore 331 heater status %s' % resp)
        return int(resp)
    
    def get_setpoint(self, loop=1):
        resp = self.ask('SETP? %d' % loop)
        if self.debug: print('Lakeshore 331 T setpoint %s' % resp)
        return float(resp)
    
    def set_setpoint(self, Tset, loop=1):
        assert Tset > 0 and isinstance(Tset, float)
        self.ask('SETP %d, %0.2f' % (loop, Tset))
    
    def get_heater_range(self):
        resp = self.ask('RANGE?')
        if self.debug: print('Lakeshore 331 heater range %s' % resp)
        return HEATER_RANGE_CHOICES[int(resp)]
    
    def set_cmode(self, val):
        assert val in CONTROL_MODES
        self.ask('CMODE 1, %d' % (CONTROL_MODES.index(val) + 1))
        
    def get_cmode(self):
        resp = self.ask('CMODE? 1')
        return CONTROL_MODES[int(resp) - 1]
        
    def get_ramp_params(self, loop=1):
        resp = self.ask(f'RAMP? {loop}')
        [onoff, rate] = resp.split(sep=',')
        return [bool(int(onoff)), float(rate)]
    
    def set_ramp_params(self, state, rate, loop=1):
        state = int(state)
        if self.debug: print(f'RAMP {loop}, {state}, {rate}')
        self.ask(f'RAMP {loop}, {state}, {rate}')
    
    def get_ramp_rate(self, loop=1):
        onoff, rate = self.get_ramp_params(loop=loop)
        return rate
    
    def get_ramp_onoff(self, loop=1):
        onoff, rate = self.get_ramp_params(loop=loop)
        return onoff
        
    def is_ramping(self, loop=1):
        resp = self.ask('RAMPST? %d' % loop)
        return bool(int(resp))
        
    def set_input_curve(self, val, inp='A'):
        self.ask('INCRV %s, %d' % (inp, SENSOR_CURVES.index(val) + 1))
        
    def get_input_curve(self, inp='A'):
        resp = self.ask('INCRV? %s' % inp)
        return SENSOR_CURVES[int(resp) - 1]
    
    def get_PID(self, loop=1):
        resp = self.ask(f'PID? {loop}')
        P, I, D = [float(x) for x in resp.split(sep=',')]
        if self.debug: print('get PID values', P, I, D)
        return [P, I, D]
    
    def set_PID(self, loop, P, I, D):
        if self.debug: print(f'set PID {loop}, {P}, {I}, {D}')
        self.ask(f'PID {loop}, {P}, {I}, {D}')
    
    def get_tune_status(self):
        resp = self.ask(f'TUNEST?')
        if self.debug:print(repr(resp), bool(int(resp)))
        return bool(int(resp))
    
    def set_cset(self, loop=1, input='A', units=1, powerup_enable=0, current_power=2):
        cmd = f'CSET {loop}, {input}, {units}, {powerup_enable}, {current_power}'
        resp = self.ask(cmd)
        if self.debug: print('Lakeshore 331 interface set_cset', cmd, resp)
        
    def get_cset(self, loop):
        cmd = f'CSET? {loop}'
        resp = self.ask(cmd)
        return resp.split(',')
        
    def reset(self):
        self.ask('*CLS')
        self.ask('*RST')

    
if __name__ == '__main__':
    tctrl = Lakeshore331Interface(debug=False)
    print(tctrl.info())
    print("T = " + str(tctrl.read_T()) + 'K')
    tctrl.set_output(enable=0, chan='B', vmax=0.0)
    print('ramp params', tctrl.get_ramp_params(1))
    tctrl.get_output()
    tctrl.close()
    
