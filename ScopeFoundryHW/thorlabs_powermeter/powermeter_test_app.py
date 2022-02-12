from ScopeFoundry import BaseMicroscopeApp

class PowerMeterApp(BaseMicroscopeApp):

    name = 'powermeter'
    
    def setup(self):
                
        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW, PowerMeterOptimizerMeasure, ThorlabsPowerMeterAnalogReadOut
        self.add_hardware(ThorlabsPowerMeterHW(self))
        self.add_hardware(ThorlabsPowerMeterAnalogReadOut(self))
        self.add_measurement(PowerMeterOptimizerMeasure(self))

if __name__ == '__main__':
    import sys
    app = PowerMeterApp(sys.argv)
    sys.exit(app.exec_())