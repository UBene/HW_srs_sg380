'''
Connexion SpaceNavigator/SpaceMouse ScopeFoundry module
@author: Alan Buckley

Suggestions for improvement from Ed Barnard. <esbarnard@lbl.gov>

'''
from ScopeFoundry.measurement import Measurement
import time
import pygame.event
from pygame.constants import JOYAXISMOTION, JOYHATMOTION, JOYBUTTONDOWN, JOYBUTTONUP
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

class Connexion_pg_MC(Measurement):

    name = "connexion_pg_mc"

    axis_map = {0: 'x',
                1: 'y',
                2: 'z',
                3: 'pitch',
                4: 'roll',
                5: 'yaw'}
    button_map = {0: 'left',
                  1: 'right'}

    def setup(self):
        """Loads UI into memory from file, connects **LoggedQuantities** to UI elements."""
        self.app
        
        self.ui_filename = sibling_path(__file__, "3D_control.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        self.dt = 0.05
        self.connexion = self.app.hardware['connexion_pg_hc']
        
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
        # self.connexion.button.connect_bidir_to_widget(
        #         self.ui.button_dsb)
        self.connexion.left.connect_bidir_to_widget(
                self.ui.left_cb)
        self.connexion.right.connect_bidir_to_widget(
                self.ui.right_cb)
        # self.connexion.left_right.connect_bidir_to_widget(
        #         self.ui.lr_cb)
        self.connexion.devices.connect_bidir_to_widget(
                self.ui.device_cb)
        

    def joystick_setup(self):
        self.joystick = self.connexion.dev.joystick
        name = self.connexion.dev.joystick_name
        self.connexion.settings.devices.change_choice_list(tuple(["{}".format(name)]))

    def run(self):
        """In this case, run is not needed since hardware level handles callbacks. Does nothing."""
        if self.connexion.dev:
            self.joystick_setup()
        while not self.interrupt_measurement_called:
            time.sleep(self.dt)
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.JOYAXISMOTION:
                    for i in range(self.connexion.dev.num_axes):
                        self.connexion.settings[self.axis_map[i]] = self.joystick.get_axis(i)
                        #print(i, self.axis_map[i], self.joystick.get_axis(i))

                elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP]:
                    button_state = (event.type == pygame.JOYBUTTONDOWN)
 
                    for i in range(self.connexion.dev.num_buttons):
                        self.connexion.settings[self.button_map[i]] = self.joystick.get_button(i)
#                         print(i, self.joystick.get_button(i))

#                         if self.joystick.get_button(i) == button_state:
#                             try:
#                                 self.controller.settings[self.button_map[i]] = button_state
#                             except KeyError:
#                                 self.log.error("Unknown button: %i (target state: %s)" % (i,
#                                     'down' if button_state else 'up'))



