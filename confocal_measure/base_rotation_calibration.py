"""
Created on Jun 8, 2021

@author: Benedikt Ursprung, Sriram Sridhar 
"""
import numpy as np
from qtpy import QtCore
from ScopeFoundryHW.flircam.flircam_live_measure import FlirCamLiveMeasure
import time


class BaseRotationCalibration:
    """
    use this class as a Base class together with other measurement class(es) that

    1. display an a live image
    2. has the following methods
        a) get_current_stage_position
        b) set_stage_position
        c) jog_rot_z
    3. make sure that this setup functions get called.
    
    see ir_microscope/measurements/stage_live_cam for an example
    """
    
    name = 'rotation_calibration'


    def setup(self):

        self.add_operation("start calibration", self.start_calib)
        self.add_operation("end calibration", self.end_calibration)
        self.add_operation("rotate", self.rotate)
        self.add_operation("move_to_center", self.move_to_center)
        self.add_operation(
            "rotate around current pos",
            lambda: self.rotate_around_current_position(None)
        )

        self.settings.New("xc", float, initial=0, spinbox_decimals=6)
        self.settings.New("yc", float, initial=0, spinbox_decimals=6)
        self.settings.New("zc", float, initial=0, spinbox_decimals=6)
        self.settings.New("angle_z", float, unit="deg", initial=5.0)

        self.end_calibration()        


    def get_current_stage_position(self):
        """Override! return x,y,z position (z can be None) """
        raise NotImplementedError(self.name + " needs get_current_stage_position function")

    def set_stage_position(self, x, y, z=None):
        """Override! sets the x,y stage position and z if applicable"""
        raise NotImplementedError(self.name + " needs a set_stage_position function")

    def jog_rot_z(self, angle_z):
        """Override! turn stage by an angle_z"""
        raise NotImplementedError(self.name + " needs a jog_rot_z function")

    def end_calibration(self):
        self.is_calibrating = False
        self.status = 'xc,yc are calib params! press "start calibration"'

    def start_calib(self):
        self.N_sample = 0
        self.rotated = False
        self.is_calibrating = True
        self.status = 'step 1/2: choose point on sample and press "rotate"'
        #self.settings["crosshairs"] = True

    def rotate(self):
        if not self.is_calibrating:
            return

        S = self.settings

        if not self.rotated:
            x0, y0, z0 = self.get_current_stage_position()
            self.positions0 = [x0, y0, z0]

            self.jog_rot_z(+180)

            self.rotated = True

            self.rotate_around_current_position(+180)
            self.status = {'text':"guessing target position based on xc, yc",
                           'color':"y"} 
            time.sleep(0.5)

            self.status = {'text':"step 2/2: find same point again",
                           'color':"y"} 
        else:
            x1, y1, z1 = self.get_current_stage_position()
            x0, y0, z0 = self.positions0

            self.N_sample += 1

            xc_new = (x1 + x0) / 2
            yc_new = (y1 + y0) / 2
            

            if self.N_sample == 1:
                S["xc"] = xc_new
                S["yc"] = yc_new
            else:
                S["xc"] = (S["xc"] * self.N_sample + xc_new) / (self.N_sample + 1)
                S["yc"] = (S["yc"] * self.N_sample + yc_new) / (self.N_sample + 1)

            print(xc_new, yc_new, S["xc"], S["yc"])

            self.jog_rot_z(-180)
            self.rotated = False
            self.status = f'{self.N_sample} successful calib pts, step 1/2: choose point on sample and press "rotate around current pos" or press "go to center"'

    def T(self, dx, dy, dz):
        return np.array([[1, 0, 0, dx], [0, 1, 0, dy], [0, 0, 1, dz], [0, 0, 0, 1]])

    def Rz(self, angle_z):
        a = np.radians(angle_z)
        return np.array(
            [
                [np.cos(a), np.sin(a), 0, 0],
                [-np.sin(a), np.cos(a), 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ]
        )

    def transformation_matrix(self, angle_z):
        angle_z = int(angle_z / 360 * 4096) / 4096.0 * 360 # Compensating for rounding errors
        dx = self.settings["xc"]
        dy = self.settings["yc"]
        dz = 0
        M = self.T(dx, dy, dz) @ (self.Rz(0 - angle_z) @ self.T(-dx, -dy, -dz))
        return M

    def rotate_around_current_position(self, angle_z=None):
        if angle_z == None:
            angle_z = self.settings["angle_z"]
        self.jog_rot_z(angle_z)
        x, y, z = self.get_current_stage_position()
        z = 0
        new_pos = self.get_rotated_stage_position(x, y, z, angle_z)
        self.set_stage_position(new_pos[0], new_pos[1], None)
        print('go around current position new pos', new_pos)

        return new_pos

    def get_rotated_stage_position(self, x, y, z, angle_z):
        M = self.transformation_matrix(angle_z)
        current_pos = np.array([x, y, z, 1])
        new_pos = M @ current_pos
        print(new_pos)
        return new_pos

    def generate_stage_positions(self, x, y, z, angle_zs=[0, 1, 2]):
        positions = []
        for angle_z in angle_zs:
            positions.append(self.get_rotated_stage_position(x, y, z, angle_z))
        return positions

    def move_to_center(self):
        S = self.settings
        self.set_stage_position(S["xc"], S["yc"])
