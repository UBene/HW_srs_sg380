from ScopeFoundry.hardware import HardwareComponent
import time
import numpy as np

class ThorlabsPAX1000_PolarimeterHW(HardwareComponent):
    
    name = 'polarimeter'
    
    N_hist = 1000
    
    def setup(self):
        
        self.settings.New("port", dtype=str, initial="auto")
        self.settings.New("wavelength", dtype=float, unit='nm')
        self.settings.New("meas_mode", dtype=str, choices=['IDLE'])
        self.settings.New("total_power", dtype=float, unit="W", si=True, ro=True)
        self.settings.New("polarized_power", dtype=float, unit="W", si=True, ro=True)
        self.settings.New("unpolarized_power", dtype=float, unit="W", si=True, ro=True)
        self.settings.New("azimuth", dtype=float, unit="deg", ro=True)
        self.settings.New("ellipticity", dtype=float, unit="deg", ro=True)
        self.settings.New("DOP", dtype=float, unit="%", ro=True)
        
    def connect(self):
        S = self.settings
        from ScopeFoundryHW.thorlabs_pax1000.pax1000_dev import ThorlabsPAX1000_Polarimeter
        
        if S['port'].startswith("auto"):
            self.pax = ThorlabsPAX1000_Polarimeter(auto_find=True, debug=S['debug_mode'])
        else:
            self.pax = ThorlabsPAX1000_Polarimeter(auto_find=False, rsrc_name = S['port'], debug=S['debug_mode'])
        
        S.meas_mode.change_choice_list(self.pax.meas_modes)
        S.meas_mode.connect_to_hardware(
            read_func = self.pax.get_measurement_mode,
            write_func = self.pax.set_measurement_mode)
        
        #S.meas_mode.update_value("HALF_512")
        S.meas_mode.read_from_hardware()
        
        S.wavelength.connect_to_hardware(
            read_func = self.pax.get_wavelength,
            write_func = self.pax.set_wavelength
            )
        S.wavelength.read_from_hardware()
        
        
        N = self.N_hist
        self.history = dict(
            timestamp = np.zeros(N, dtype=np.uint32),
            total_power = np.zeros(N, dtype=float),
            polarized_power = np.zeros(N, dtype=float),
            unpolarized_power = np.zeros(N, dtype=float),
            azimuth = np.zeros(N, dtype=float),
            ellipticity = np.zeros(N, dtype=float),
            DOP = np.zeros(N, dtype=float),
            #Stokes = np.zeros( (N,4), dtype=float),
            )
    
    
    def threaded_update(self):
        time.sleep(0.010)
        
        if self.settings['meas_mode'] != "IDLE":
            try:
                x = self.pax.get_scan()
                self.settings['total_power'] = x['total_power']
                self.settings['polarized_power'] = x['polarized_power']
                self.settings['unpolarized_power'] = x['unpolarized_power']
                self.settings['azimuth'] = x['azimuth']*180./np.pi
                self.settings['ellipticity'] = x['ellipticity']*180./np.pi
                self.settings['DOP'] = x['DOP']*100.0
                
                def roll_and_store_history(name, new_val):
                    self.history[name] = np.roll(self.history[name], 1)
                    self.history[name][0] = new_val
                    
                roll_and_store_history("timestamp", x["timestamp"])
                roll_and_store_history("total_power", x["total_power"])
                #roll_and_store_history("Stokes", x["Stokes"])
                roll_and_store_history("azimuth",  x['azimuth']*180./np.pi)
                roll_and_store_history("ellipticity",  x['ellipticity']*180./np.pi)
                roll_and_store_history("DOP", x["DOP"]*100.)
                
                #print(x['StokesNormalized'])
                #print(x['Stokes'])
                
            except:
                pass
        
        
        
    def disconnect(self):
        
        if hasattr(self, 'pax'):
            self.pax.close()
            del self.pax
            
        self.settings.disconnect_all_from_hardware()
        
        
