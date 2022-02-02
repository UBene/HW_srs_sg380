from ScopeFoundry import BaseMicroscopeApp

class PowerMeterApp(BaseMicroscopeApp):

    name = 'powermeter'
    
    def setup(self):
        
        #self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'trpl_quick_access.ui')))
        
        
        
        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW, PowerMeterOptimizerMeasure
        self.add_hardware(ThorlabsPowerMeterHW(self))
        self.add_measurement(PowerMeterOptimizerMeasure(self))

        #self.settings_load_ini('uv_defaults.ini')

if __name__ == '__main__':
    import sys
    app = PowerMeterApp(sys.argv)
    sys.exit(app.exec_())