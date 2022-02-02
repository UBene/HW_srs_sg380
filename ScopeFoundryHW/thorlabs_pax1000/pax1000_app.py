from ScopeFoundry import BaseMicroscopeApp

class PAXApp(BaseMicroscopeApp):

    name = 'powermeter'
    
    def setup(self):
        
        #self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'trpl_quick_access.ui')))
        
        
        
        from ScopeFoundryHW.thorlabs_pax1000.pax1000_hw import ThorlabsPAX1000_PolarimeterHW
        pax = self.add_hardware(ThorlabsPAX1000_PolarimeterHW(self))

        pax.settings['port'] = "USB::0x1313::0x8031::M00559829::INSTR"

        
        #self.settings_load_ini('uv_defaults.ini')

if __name__ == '__main__':
    import sys
    app = PAXApp(sys.argv)
    sys.exit(app.exec_())