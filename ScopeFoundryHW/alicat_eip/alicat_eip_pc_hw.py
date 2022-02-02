from ScopeFoundry.hardware import HardwareComponent
import struct

class Alicat_EIP_PC_HW(HardwareComponent):
    
    """ Alicat Pressure Controller over EtherNet/IP
    
        uses the cpppo library to communicate
        
        Tested with Alicat PC-15PSIA-D-EIP/DS
        
    """
    
    name = 'alicat_pc'

    def __init__(self, app, debug=False, name=None, pressure_unit='PSIA'):
        self.pressure_unit = pressure_unit
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    
    def setup(self):
        
        self.settings.New("address", dtype=str, initial='192.168.2.101')
        
        self.settings.New("serial_num", dtype=int, ro=True)
        self.settings.New("gas", dtype=str, ro=True)
        
        self.settings.New("setpoint", dtype=float, unit=self.pressure_unit, initial=0, spinbox_decimals=3)
        
        # Pressure Controller specific
        self.settings.New("pressure", dtype=float, unit=self.pressure_unit, ro=True, spinbox_decimals=2)
        
        self.add_operation('read_state', self.read_state)
    
    def connect(self):
        
        from cpppo.server.enip.get_attribute import proxy_simple

        self.p = proxy_simple( self.settings['address'] )
        
        self.settings.setpoint.connect_to_hardware(
            read_func = self.read_setpoint,
            write_func = self.write_setpoint
            )
        
        
        self.settings['serial_num'] = list(self.p.read( [('@1/1/6','UDINT')] ))[0][0]
        
        self.settings.setpoint.read_from_hardware()
        self.read_state()
        
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'p'):
            del self.p
        
        
    def read_setpoint(self):
        return list(self.p.read( [('@4/100/3','REAL')] ))[0][0]
        
    def write_setpoint(self, sp):
        list(self.p.read( [('@4/100/3 = {}'.format(float(sp)),'REAL')] ))
        
        
    def read_state(self):
        """Update settings (pressure, etc) based on hardware state
        """
        try:
            dat = bytes(list(self.p.read( [('@4/101/3','USINT')] ))[0])
        except ConnectionAbortedError as err:
            print("failed to communicate to {}. Retrying".format(self.name))
            self.disconnect()
            self.connect()
            dat = bytes(list(self.p.read( [('@4/101/3','USINT')] ))[0])


        x = struct.unpack("<HIff", dat)

        S  = self.settings

        gas_num = x[0]
        #print("gas", gas_num, gas_list[gas_num])
        S['gas'] = gas_list[gas_num]
        device_status = x[1]
        S['pressure'] = x[2]
        mass_flow_sp = x[3]
        

gas_list = {        
    0: "Air Air",
    1: "Argon Ar",
    2: "Methane CH4",
    3: "Carbon Monoxide CO",
    4: "Carbon Dioxide CO2",
    5: "Ethane C2H6",
    6: "Hydrogen H2",
    7: "Helium He",
    8: "Nitrogen N2",
    9: "Nitrous Oxide N2O",
    10: "Neon Ne",
    11: "Oxygen O2",
    12: "Propane C3H8",
    13: "normal-Butane n-C4H10",
    14: "Acetylene C2H2",
    15: "Ethylene C2H4",
    16: "iso-Butane i-C4H10",
    17: "Krypton Kr",
    18: "Xenon Xe",
    19: "Sulfur Hexafluoride SF6",
    20: "75%Ar / 25% CO2 C-25",
    21: "90% Ar / 10% CO2 C-10",
    22: "92% Ar / 8% CO2 C-8",
    23: "98% Ar / 2% CO2 C-2",
}