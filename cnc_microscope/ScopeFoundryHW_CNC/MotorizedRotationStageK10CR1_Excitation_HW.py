#
"""
Created on Feb 22 2019

By Xinyi Xu

"""

from ScopeFoundry import HardwareComponent
from cnc_microscope.ScopeFoundryEquipment.MotorizedRotationStageK10CR1_Collection_Equipment import MotorizedStage

class MotorizedStage_Excitation_HW(HardwareComponent):

    name = "MotorizedStageExcitation"
    debug = False


    def setup(self):

        self.debug = True


        #Create logged quantities
        deg_pos = dict(  dtype=float, ro=True,
                           initial = 0,
                           spinbox_decimals=2,
                           vmin=-2160,
                           vmax=2160,
                           unit='deg')

        self.deg_pos = self.add_logged_quantity("Current Pos", **deg_pos)

        deg_target = dict(  dtype=float, ro=False,
                           initial = 0,
                           spinbox_decimals=2,
                           vmin=-2160,
                           vmax=2160,
                           unit='deg')

        self.deg_target = self.add_logged_quantity("Target Pos", **deg_target)

        deg_steps = dict(  dtype=float, ro=False,
                           initial = 0,
                           spinbox_decimals=2,
                           vmin=0,
                           vmax=2160,
                           unit='deg')

        self.deg_step = self.add_logged_quantity("deg_step", **deg_steps)

        self.add_operation("Go_to_Pos", self.go_to_pos)
        self.add_operation("Back_to_Zero", self.homing_zero)
        self.add_operation("move_clockwise", self.move_clk)
        self.add_operation("move_ctclockwise", self.move_ctclk)

    def connect(self):

        # Create a Motorized_Stage_Excitation
        self.Motorized_Stage_Excitation = MotorizedStage(sn=b'55902790')
        self.Motorized_Stage_Excitation.initialize()

        # Connect to the logged quantities
        self.deg_pos.hardware_read_func = self.Motorized_Stage_Excitation.current_pos

        self.read_from_hardware()
        print('connected to', self.name)




    def disconnect(self):

        # disconnect_exit
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
    
        if hasattr(self, 'Motorized_Stage_Excitation'):
            #disconnect hardware
            self.Motorized_Stage_Excitation.close()
            
            # clean up hardware object
            del self.Motorized_Stage_Excitation
        
        print('disconnected ',self.name)
        
        
        






    def homing_zero(self):
        self.Motorized_Stage_Excitation.homing()

    def go_to_pos(self):
        self.Motorized_Stage_Excitation.go_to_pos(self.deg_target.value)

    def move_clk(self):
        self.Motorized_Stage_Excitation.move_clockwise(self.deg_step.value)

    def move_ctclk(self):
        self.Motorized_Stage_Excitation.move_counterclockwise(self.deg_step.value)

    def stop_immediate(self):
        self.Motorized_Stage_Excitation.StopImmediate()





