"""
Created on Mar 21, 2022

@author: Benedikt Ursprung
"""
from ScopeFoundry.hardware import HardwareComponent


def bool2str(v):
    return str(int(v))


def str2bool(v):
    return {"0": False, "1": True}[v]


MODULATIONTYPES = (
    ("AM", 0),
    ("FM", 1),
    ("PhaseM", 2),
    ("Sweep", 3),
    ("Pulse", 4),
    ("Blank", 5),
    ("IQ", 6))

QFNC = (("Noise", 4), ("External", 5))


class SG380_HW(HardwareComponent):
    '''
    ScopeFoundry Hardware interface for SRS SG380 series
    ToDo: Fix error handling
    '''
    
    name = "srs_sg380"

    def __init__(self, app, debug=False, name=None, max_dBm=9):
        self.max_dBm = max_dBm
        HardwareComponent.__init__(self, app, debug, name)

    def setup(self):
        S = self.settings
        S.New("port", str, initial="COM1") #GPIB0::27::INSTR
        S.New('model', str, ro=True)
        S.New('serial', str, ro=True)
        S.New('error', str, ro=True)
        S.New("output", bool, initial=False)
        S.New("frequency", unit="Hz", si=True)
        S.New("amplitude", float, unit="dBm", vmax=self.max_dBm)
        S.New("modulation", bool, initial=False)
        S.New("modulation_type", int, choices=MODULATIONTYPES)
        S.New("QFNC", str, initial=5, choices=QFNC,
              description='the modulation function for IQ modulation',
              )

    def connect(self):

        S = self.settings

        print(S["port"])

        #Option A Using GPIB
        # import pyvisa
        # rm = pyvisa.ResourceManager()
        # self.dev = rm.open_resource(S["port"])

        # Option B Using RS232
        from .rs232_dev import RS232_Dev
        self.dev = RS232_Dev(S["port"])

        self.read_ID()
        self.clear_status()

        #
        S.output.connect_to_hardware(
            self.read_enable_output, self.write_enable_output)
        S.frequency.connect_to_hardware(
            self.read_frequency, self.write_frequency)
        S.amplitude.connect_to_hardware(
            self.read_amplitude, self.write_amplitude)
        S.modulation.connect_to_hardware(
            self.read_enable_modulation, self.write_enable_modulation)
        S.modulation_type.connect_to_hardware(self.read_type, self.write_type)
        S.QFNC.connect_to_hardware(self.read_qfnc, self.write_qfnc)
        self.read_from_hardware()
        #self.read_error()

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            self.settings['model'] = 'not_connected'
            self.settings['serial'] = 'not_connected'

    def ask(self, cmd):
        resp = self.dev.query(cmd)
        if self.settings['debug_mode']:
            print(f"{self.name} asked {cmd}: {repr(resp)}")
        #self.read_error()
        return resp.strip('\r\n')

    def write(self, cmd):
        if self.settings['debug_mode']:
            print(self.name, 'write', cmd)
        self.dev.write(cmd)
        #self.read_error()

    def read_error(self):
        return 0
        err = self.dev.query("LERR?")
        if int(err) == 0:
            self.settings['error'] = 'no error'
        else:
            self.settings['error'] = str(err)
        return int(err)

    def read_ID(self):
        device_ID = self.ask('*IDN?')
        company, model, serial, ver = device_ID.split(',')
        self.settings['model'] = model
        self.settings['serial'] = serial[3:]
        return device_ID

    def write_enable_output(self, enable):
        a = bool2str(enable)
        self.write(f"ENBR {a}")

    def read_enable_output(self):
        return str2bool(self.ask("ENBR?"))

    def read_frequency(self):
        resp = self.ask("FREQ?")
        return resp

    def write_frequency(self, freq, units="Hz"):
        self.write(f"FREQ {freq} {units}")

    def read_amplitude(self):
        resp = self.ask("AMPR?")
        return resp

    def write_amplitude(self, amplitude):
        if amplitude >= self.max_dBm:
            print(
                self.name, f'Warning: did not write amplitude >{self.max_dBm} dBm', amplitude)
        else:
            self.write(f"AMPR {amplitude} dBm")

    def write_enable_modulation(self, enable: bool):
        self.write(f"MODL {bool2str(enable)}")

    def read_enable_modulation(self):
        return str2bool(self.ask("MODL?"))

    def read_type(self):
        return self.ask("TYPE?")

    def write_type(self, _type: int):
        self.write(f"TYPE {_type}")

    def read_qfnc(self):
        return self.ask("QFNC?")

    def write_qfnc(self, val):
        self.write(f"QFNC {val}")
        
    def restore_defaults(self):
        self.dev.write("*RST")
                
    def clear_status(self):
        self.dev.write("*CLS")

