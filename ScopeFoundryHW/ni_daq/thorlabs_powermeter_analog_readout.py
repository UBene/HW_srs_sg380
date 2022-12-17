from ScopeFoundry import HardwareComponent


class ThorlabsPowerMeterAnalogReadOut(HardwareComponent):

    name = 'thorlabs_powermeter_analog_readout'

    def setup(self):

        self.power = self.settings.New(name='power', dtype=float,
                                       si=True,
                                       unit="W", vmin=0, vmax=10,
                                       ro=True)
        self.voltage = self.settings.New(name='voltage', dtype=float,
                                         si=True,
                                         unit="V", vmin=-10, vmax=10,
                                         ro=True)

        self.power_range = self.settings.New(name='power_range',
                                             dtype=float, unit="W",
                                             vmin=0, vmax=10, ro=True)

    def connect(self):
        from ScopeFoundryHW.ni_daq import NI_AdcTask
        if self.debug_mode.val:
            self.log.debug("connecting to {}".format(self.name))

        # Open connection to hardware
        self.adc = NI_AdcTask(channel='/Dev1/ai2', range=10,
                              name=self.name, terminalConfig='rse')
        self.adc.set_single()
        self.adc.start()

        # Connect lq to hardware
        self.voltage.hardware_read_func = self.read_adc_single

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()

        # disconnect hardware
        self.adc.close()

        # clean up hardware object
        del self.adc

    def read_adc_single(self):
        resp = self.adc.get()
        if self.debug_mode.val:
            self.log.debug("read_adc_single resp: {}".format(resp))
        return float(resp[0])
