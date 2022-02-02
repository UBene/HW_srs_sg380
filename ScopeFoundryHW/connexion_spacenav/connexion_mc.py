'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
from ScopeFoundry.measurement import Measurement
from time import sleep
from msvcrt import kbhit

from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

class Connexion_MC(Measurement):

    name = "connexion_mc"

    def setup(self):
        """Loads UI into memory from file, connects **LoggedQuantities** to UI elements."""
        self.app
        
        self.ui_filename = sibling_path(__file__, "3D_control.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        self.connexion = self.app.hardware['connexion_hc']
        
        self.connexion.x.connect_bidir_to_widget(
                self.ui.x_dsb)
        self.connexion.y.connect_bidir_to_widget(
                self.ui.y_dsb)
        self.connexion.z.connect_bidir_to_widget(
                self.ui.z_dsb)
        self.connexion.roll.connect_bidir_to_widget(
                self.ui.roll_dsb)
        self.connexion.pitch.connect_bidir_to_widget(
                self.ui.pitch_dsb)
        self.connexion.yaw.connect_bidir_to_widget(
                self.ui.yaw_dsb)
        self.connexion.button.connect_bidir_to_widget(
                self.ui.button_dsb)
        self.connexion.left.connect_bidir_to_widget(
                self.ui.left_cb)
        self.connexion.right.connect_bidir_to_widget(
                self.ui.right_cb)
        self.connexion.left_right.connect_bidir_to_widget(
                self.ui.lr_cb)
        self.connexion.devices.connect_bidir_to_widget(
                self.ui.device_cb)


    def run(self):
        """In this case, run is not needed since hardware level handles callbacks. Does nothing."""
        while not self.interrupt_measurement_called:
            sleep(0.05)
                


