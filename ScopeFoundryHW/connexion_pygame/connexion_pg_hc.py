'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.connexion_pygame.connexion_pg_ec import ConnexionDevice


class Connexion_pg_HC(HardwareComponent):

    name = "connexion_pg_hc"

    def setup(self):


        """Defines logged quantities upon startup."""
        self.x = self.settings.New(name='x', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.y = self.settings.New(name='y', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.z = self.settings.New(name='z', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.roll = self.settings.New(name='roll', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.pitch = self.settings.New(name='pitch', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.yaw = self.settings.New(name='yaw', initial=0,
                                            dtype=float, fmt="%.2f", 
                                            ro=True, vmin=-1.0, vmax=1.0)
        self.button = self.settings.New(name='button', initial=0, dtype=int, fmt="%i",
                                            ro=True, vmin=0, vmax=3)
        self.left = self.settings.New(name='left', initial=0, dtype=bool,
                                            ro=True)
        self.right = self.settings.New(name='right', initial=0, dtype=bool,
                                            ro=True)
        self.devices = self.settings.New(name='devices', initial=None, dtype=str, choices = [])

        self.axis_profile = None
        self.button_profile = None
        self.button_map = None
        
    def connect(self):
        """Connects to equipment level module, 
        loads the appropriate key map into memory,
        opens the selected device, sets data handler."""
        self.dev = ConnexionDevice()
            
    def disconnect(self):
        """Hardware disconnect and cleanup function."""
        self.dev.close()
        del self.dev

