'''
Created on Jan 15, 2023

@author: Benedikt Ursprung
'''
from ScopeFoundry.hardware import HardwareComponent
import pyvisa


class TektronixScopeHW(HardwareComponent):

    name = 'tektronix_scope'

    def setup(self):
        S = self.settings
        S.New('port', str, initial='USB::0x0699::0x0408::C052480::INSTR')

    def connect(self):

        S = self.settings
        self.visa_resource_manager = pyvisa.ResourceManager()
        if S['debug_mode']:
            print('Visa devices detected:',
                  self.visa_resource_manager.list_resources())
        self.dev = self.visa_resource_manager.open_resource(S['port'])

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

    def write(self, cmd):
        if self.settings['debug_mode']:
            print(self.name, 'write', cmd)
        self.dev.write(cmd)

    def ask(self, cmd):
        if self.settings['debug_mode']:
            print(self.name, 'ask', cmd)
        return self.dev.query(cmd)
