from ScopeFoundry import HardwareComponent

try:
    from equipment.srslockin import SRSlockin
except Exception as err:
    print "Cannot load required modules for SRSLockin:", err


SRSPort = 'COM12'

class SRSLockinComponent(HardwareComponent): 
    

    name = 'srs_lockin'
    debug = False    

    def setup(self):
        self.debug = True
        
        self.frequency = self.add_logged_quantity('f', dtype=float, unit='Hz', ro=True)
        self.current = self.add_logged_quantity('i', dtype=float, unit='A', ro=True)
        
        self.sensitivity = self.add_logged_quantity('sensitivity', 
                                                    dtype=str, choices = [('','')],
                                                    ro=False)
        
    def connect(self):
        if self.debug: print "connecting to SRS lockin"
        
        # Open connection to hardware
        self.srs = SRSlockin(port=SRSPort, debug=True)
        
        # connect logged quantities
        self.frequency.hardware_read_func = \
            self.srs.get_frequency
        self.current.hardware_read_func = \
            self.srs.get_signal
            
        self.sensitivity.hardware_read_func = self.srs.get_sensitivity
        
        self.sensitivity.change_choice_list(zip(self.srs.sensitivities, self.srs.sensitivities))

        self.sensitivity.hardware_set_func = self.srs.set_sensitivity
        
        print 'connected to ',self.name

    def disconnect(self):

        # disconnect logged quantities from hardware
        # ///\
    
        #disconnect hardware
        self.srs.close()
        
        # clean up hardware object
        del self.srs
        
        print 'disconnected ',self.name
          
            