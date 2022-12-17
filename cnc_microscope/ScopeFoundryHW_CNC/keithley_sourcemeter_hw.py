'''
Kaiyuan Yao
12/08/2018

'''
from ScopeFoundry import HardwareComponent

try:
    from ScopeFoundryEquipment.keithley_sourcemeter import KeithleySourceMeter
except Exception as err:
    print ("Cannot load required modules for Keithley SourceMeter:", err)



###########
KeithleyPort = "GPIB::23"

class KeithleySourceMeterComponent(HardwareComponent): #object-->HardwareComponent
    
    name = 'keithley_sourcemeter'
    debug = False
    
    def setup(self):
        self.debug = True
        
        self.source_mode = self.add_logged_quantity('source_mode', dtype=str, initial = 'voltage') #'VOLT' or 'CURR'
        self.source_enabled = self.add_logged_quantity('source_enabled', dtype=bool, ro=True, initial=False)
        
        #self.V_meas = self.add_logged_quantity('V_meas', dtype=float, unit='V', ro=True, si=True)
        #self.I_meas = self.add_logged_quantity('I_meas', dtype=float, unit='A', ro=True, si=True)
        self.V_source  = self.add_logged_quantity('V_source', dtype=float, unit='V', ro=False, si=True, initial = 0)
        self.I_source  = self.add_logged_quantity('I_source', dtype=float, unit='A', ro=False, si=True, initial = 0)
        
        self.add_operation("Turn On Source", self.turn_on_source)
        self.add_operation("TUrn_Off Source", self.turn_off_source)
        self.add_operation("AutoRange", self.autorange)
        self.add_operation("Reset", self.reset_keithley)
        
        self.add_operation('Measure current', self.measure_current_hw)
        self.add_operation('Measure voltage', self.measure_voltage_hw)
        
    def connect(self):
        if self.debug: print ("connecting to keithley sourcemeter")
        
        # Open connection to hardware
        self.keithley = KeithleySourceMeter(port=KeithleyPort, debug=True)
        
        # Get and print ID
        self.ID = self.keithley.get_ID()
        print (self.ID)
        
        # connect logged quantities
        self.source_mode.hardware_read_func = self.keithley.read_source_mode
        self.source_mode.hardware_set_func = self.keithley.set_source_mode
        self.source_enabled.hardware_read_func = self.keithley.read_source_enabled
        
        #self.V_meas.hardware_read_func = self.keithley.read_voltage
        #self.I_meas.hardware_read_func = self.keithley.read_current
        self.V_source.hardware_set_func = self.keithley.set_source_voltage
        self.I_source.hardware_set_func = self.keithley.set_source_current
        
        print ('connected to ',self.name)    

    def disconnect(self):

        # disconnect logged quantities from hardware
        # ///\
    
        #disconnect hardware
        
        if hasattr(self, 'keithley'):
            self.keithley.close()
        
            # clean up hardware object
            del self.keithley
        
        print ('disconnected ',self.name)
        
    def turn_on_source(self):
        self.keithley.enable_source()
        
    def turn_off_source(self):
        self.keithley.disable_source()
        
    def autorange(self):
        self.keithley.set_auto_range()
        
    def reset_keithley(self):
        self.keithley.reset()
        
    def measure_current_hw(self):
        print( 'HW Current Measure Result: ', self.keithley.read_current()  )
        
    def measure_voltage_hw(self):
        print( 'HW Voltage Measure Result: ', self.keithley.read_voltage()  )
                
        
        

        

