"""
Benedikt Ursprung
"""
from ScopeFoundry import HardwareComponent
from .thorlabsMFF_device import ThorlabsMFFDev
from bidict import bidict
import time

class ThorlabsMFFHW(HardwareComponent):

    def setup(self):
        self.name = "thorlabs_MFF"
        
        self.settings.New('serial_num', dtype=int, initial=37874816)
        # Create logged quantities        
        self.settings.New("pos", dtype=str, choices = ('spectrometer','apd'))
        
        self.add_operation('Toggle', self.toggle_position)       
        
        
        self.position_map = {'spectrometer':2, 'apd':1}
        self.position_map_inv = {v:k for k,v in self.position_map.items()}
        
    def connect(self):
        """Connects logged quantities to hardware write functions with :meth:`connect_to_hardware` (:class:`LoggedQuantity`)"""
        if self.debug_mode.val: self.log.debug( "Connecting to thorlabsMFF(debug)" )

        
        self.dev = ThorlabsMFFDev(sernum = self.settings['serial_num'], debug=self.settings['debug_mode'])
        

        self.settings.pos.connect_to_hardware(
            read_func=self.get_pos,
            write_func=self.move_pos_wait)

        time.sleep(0.2)
        self.read_from_hardware()


    def get_pos(self):
        pos = self.dev.get_pos()
        return self.position_map_inv[pos]
    
    def move_pos_wait(self, pos):
        self.dev.move_pos_wait(self.position_map[pos])


    def disconnect(self):
        """
        Disconnects logged quantities from hardware objects.
        :returns: None
        """
        self.settings.disconnect_all_from_hardware()
        
        # clean up hardware object
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
            
            
    def toggle_position(self):
        
        pos = self.settings.pos.read_from_hardware()
        switch_vals = [v for v in self.position_map_inv.values()]
        switch_dict = {switch_vals[0]:switch_vals[1], 
                       switch_vals[1]:switch_vals[0]}        
        self.settings['pos'] = switch_dict[pos]
        pos = self.settings.pos.read_from_hardware()
