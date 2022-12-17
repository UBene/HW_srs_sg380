from ScopeFoundry.base_app import BaseMicroscopeApp


class TestApp(BaseMicroscopeApp):
    
    name = 'test_app'
    
    def setup(self):

        rainbow = '''qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 100), 
                        stop:0.166 rgba(255, 255, 0, 100), stop:0.333 rgba(0, 255, 0, 100), stop:0.5 rgba(0, 255, 255, 100), 
                        stop:0.666 rgba(0, 0, 255, 100), stop:0.833 rgba(255, 0, 255, 100), stop:1 rgba(255, 0, 0, 100))'''

        from ScopeFoundryHW.flip_mirror_arduino import FlipMirrorHW        
        hw = self.add_hardware(FlipMirrorHW(self, choices=['Spectrometer', 'APD'], 
                                            colors=[rainbow, None]),
                               )
                                                                                        
        hw.settings['port'] = 'COM5'
        hw.settings['connected'] = True

        
if __name__ == '__main__':

    import sys
    app = TestApp(sys.argv)
    sys.exit(app.exec_())
