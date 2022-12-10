'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
from .web_sq_control.WebSQControl import WebSQControl
from ScopeFoundry.hardware import HardwareComponent


import numpy as np


class SNSPDHW(HardwareComponent):

    name = 'snspd'

    def __init__(self, app, debug=False, name=None, max_number_of_detectors=8):
        self.max_number_of_detectors = max_number_of_detectors
        super().__init__(app, debug, name)

    def setup(self):

        S = self.settings
        S.New('tcp_ip_address', str, initial='192.168.1.1')
        S.New('control_port', int, initial=12000)
        S.New('counts_port', int, initial=12345)
        S.New('number_of_detectors', int, initial=0, ro=True)
        S.New('measurement_periode', int, unit='ms')
        S.New('enable_detectors', bool, initial=False)

        self.add_operation('auto_bias_exposure', self.auto_bias_exposure)
        self.add_operation('read_bias_currents', self.read_bias_currents)
        self.add_operation('write_bias_currents', self.write_bias_currents)
        self.add_operation('read_trigger_levels', self.read_trigger_levels)
        self.add_operation('write_trigger_levels', self.write_trigger_levels)
        self.add_operation('read_bias_voltages', self.read_bias_voltages)

        #self.add_operation('read counts', self.dev.acquire_cnts)

        for i in range(self.max_number_of_detectors):
            S.New(f'bias_current_{i}', float, vmin=0, vmax=32, unit='uA')
            S.New(f'trigger_level_{i}', float, vmin=0, vmax=32, unit='mV')

    def connect(self):

        S = self.settings
        self.dev = websq = WebSQControl(
            TCP_IP_ADR=S['tcp_ip_address'], CONTROL_PORT=S['control_port'], COUNTS_PORT=S['counts_port'])
        websq.connect()

        S.enable_detectors.connect_to_hardware(
            websq.get_enable_detectors, websq.enable_detectors)
        S.number_of_detectors.connect_to_hardware(
            websq.get_number_of_detectors)
        S.measurement_periode.connect_to_hardware(
            websq.get_measurement_periode, websq.set_measurement_periode)

        for i in range(self.max_number_of_detectors):
            S.get_lq(f'bias_current_{i}').connect_to_hardware(
                write_func=lambda x: self.write_bias_currents)
            S.get_lq(f'trigger_level_{i}').connect_to_hardware(
                write_func=lambda x: self.write_trigger_levels)

        self.read_from_hardware()
        self.read_trigger_levels()
        self.read_bias_currents()

    def auto_bias_exposure(self):
        if self.settings['debug_mode']:
            self.log.info(
                "Automatically finding bias current, avoid Light exposure")
        found_bias_current = self.dev.auto_bias_calibration(
            DarkCounts=[100, 100, 100, 100])
        if self.settings['debug_mode']:
            self.log.info("Bias current: " + str(found_bias_current))
        self.read_bias_currents()
        return found_bias_current

    def _list(self, quantity_name='trigger_level'):
        N = self.settings.number_of_detectors.read_from_hardware()
        return [self.settings[f'{quantity_name}_{i}'] for i in range(N)]

    def read_trigger_levels(self):
        values = self.dev.get_trigger_level()
        if self.settings['debug_mode']:
            print('read_trigger_levels:', values)
        for i, value in enumerate(values):
            self.settings[f'trigger_level_{i}'] = value
        return values

    def write_trigger_levels(self):
        trig = self._list('trigger_level')
        self.dev.set_trigger_level(trigger_level_mV=trig)

    def read_bias_currents(self):
        values = self.dev.get_bias_current()
        if self.settings['debug_mode']:
            print('read_bias_currents:', values)
        for i, value in enumerate(values):
            self.settings[f'bias_current_{i}'] = value
        return values

    def write_bias_currents(self):
        curr = self._list('bias_current')
        self.dev.set_trigger_level(current_in_uA=curr)

    def read_bias_voltages(self):
        volts = self.dev.get_bias_voltage()
        if self.settings['debug_mode']:
            print('bias_voltages:', volts)
        return volts

    def buffered_counts(self):
        data = np.array(self.dev.cnts.cnts)
        t = data[:, 0]
        cnts = data[:, 1:]
        return t, cnts

    def buffered_count_rates(self):
        periode = self.dev.get_measurement_periode() / 1000  # in sec
        t, cnts = self.buffered_counts()
        return t, cnts / periode

    def acquire_cnts(self, n):
        '''wait until n counts are aquired and return timestamps and values'''
        data = np.array(self.dev.acquire_cnts(n))
        t = data[:, 0]
        cnts = data[:, 1:]
        return t, cnts

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()  # not needed since the with closes the connection
