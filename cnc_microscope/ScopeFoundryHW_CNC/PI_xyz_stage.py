'''
Created on Jul 27, 2014

@author: Edward Barnard
'''
from __future__ import absolute_import, print_function, division
from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryEquipment.pi_nanopositioner_jog_test_3 import PINanopositioner
except Exception as err:
    print("Cannot load required modules for PIXYZStage:", err)
from qtpy import QtCore


class PIXYZStageHW(HardwareComponent):
    
    def setup(self):
        self.name = 'PI_xyz_stage'
        
        
        self.add_operation("Pointing Mode", self.move_to_pt)
        # Created logged quantities
        lq_params = dict(  dtype=float, ro=True,
                           initial = 1,
                           spinbox_decimals=3,
                           vmin=-10,
                           vmax=190,
                           si = False,
                           unit='um')
        self.x_position = self.add_logged_quantity("x_position", **lq_params)
        self.y_position = self.add_logged_quantity("y_position", **lq_params)       
        self.z_position = self.add_logged_quantity("z_position", **lq_params)
        
        lq_params = dict(  dtype=float, ro=False,
                           initial = 1,
                           spinbox_decimals=3,
                           vmin=10,
                           vmax=190,
                           unit='um')
        self.x_target = self.add_logged_quantity("x_target", **lq_params)
        self.y_target = self.add_logged_quantity("y_target", **lq_params)       
        self.z_target = self.add_logged_quantity("z_target", **lq_params)        
        
        
        lq_params = dict(unit="um", dtype=float, ro=True, initial=200, 
                         spinbox_decimals=3,
                         si=False)
        self.x_max = self.add_logged_quantity("x_max", **lq_params)
        self.y_max = self.add_logged_quantity("y_max", **lq_params)
        self.z_max = self.add_logged_quantity("z_max", **lq_params)

        lq_params = dict(dtype=str, choices=[("X","X"), ("Y","Y"),("Z","Z")])
        self.h_axis = self.add_logged_quantity("h_axis", initial="X", **lq_params)
        self.v_axis = self.add_logged_quantity("v_axis", initial="Y", **lq_params)
        
        ###Is this working?
        self.PI_AXIS_ID = dict(X = 1, Y = 2, Z = 3)
        self.xyz_axis_map = self.add_logged_quantity('xyz_axis_map', dtype=str, initial='123')
        self.xyz_axis_map.updated_value.connect(self.on_update_xyz_axis_map)
        
        
        self.add_operation("Jogging Mode", self.move_in_vel)
        
        xy_vel_lq = dict(dtype = float, ro = False,
                         initial = 0,
                         spinbox_decimals = 3,
                         vmin = 0,
                         vmax = 100,
                         unit = 'um/s')
        self.xy_vel = self.add_logged_quantity("XY Velocity", **xy_vel_lq)
        
        z_comp_lq = dict(dtype = float, ro = False,
                         initial = 0,
                         spinbox_decimals = 4,
                         vmin = -1,
                         vmax = 1)
        self.xz_ratio = self.add_logged_quantity("delta(x/z)", **z_comp_lq)
        self.yz_ratio = self.add_logged_quantity("delta(y/z)", **z_comp_lq)     
        
        self.add_operation("Jog", self.jog)
        
        #self.add_operation("Jog", self.jog)   
        #self.move_speed = self.add_logged_quantity(name='move_speed',
        #                                                     initial = 100.0,
        #                                                     unit = "um/s",
        #                                                     vmin = 1e-4,
        #                                                     vmax = 1000,
        #                                                     si = False,
        #                                                     dtype=float)        
        
        # connect logged quantities together
        self.x_target.updated_value[()].connect(self.read_pos)
        self.y_target.updated_value[()].connect(self.read_pos)
        self.z_target.updated_value[()].connect(self.read_pos)
        
    def on_update_xyz_axis_map(self):
        print("on_update_xyz_axis_map")
        map_str = self.xyz_axis_map.val
        self.PI_AXIS_ID['X'] = int(map_str[0])
        self.PI_AXIS_ID['Y'] = int(map_str[1])
        self.PI_AXIS_ID['Z'] = int(map_str[2])
    
    def move_pos_slow(self, x=None,y=None,z=None):
        # move slowly to new position
        new_pos = [None, None,None]
        new_pos[self.PI_AXIS_ID['X']-1] = x
        new_pos[self.PI_AXIS_ID['Y']-1] = y
        new_pos[self.PI_AXIS_ID['Z']-1] = z
        if self.nanopositioner.num_axes < 3:
            new_pos[2] = None
        self.nanopositioner.set_pos_slow(*new_pos)

        self.read_pos()

        
    def move_pos_fast(self,  x=None,y=None,z=None):
        new_pos = [None, None,None]
        new_pos[self.PI_AXIS_ID['X']-1] = x
        new_pos[self.PI_AXIS_ID['Y']-1] = y
        new_pos[self.PI_AXIS_ID['Z']-1] = z
        if self.nanopositioner.num_axes < 3:
            new_pos[2] = None
            
        self.nanopositioner.set_pos_fast(*new_pos)

    
    @QtCore.Slot()
    def read_pos(self):
        self.log.debug("read_pos")
        if self.settings['connected']:
            self.x_position.read_from_hardware()
            self.y_position.read_from_hardware()
            if self.nanopositioner.num_axes > 2:
                self.z_position.read_from_hardware()
        
    def connect(self):
        if self.debug_mode.val: print("connecting to PI_xyz_stage")
        
        self.nanopositioner = PINanopositioner(debug=self.debug_mode.val)
                        
        self.x_position.hardware_read_func = \
            lambda: self.nanopositioner.get_pos_ax(int(self.PI_AXIS_ID["X"]))
        self.y_position.hardware_read_func = \
            lambda: self.nanopositioner.get_pos_ax(int(self.PI_AXIS_ID["Y"]))
        if self.nanopositioner.num_axes > 2:
            self.z_position.hardware_read_func = \
                lambda: self.nanopositioner.get_pos_ax(self.PI_AXIS_ID["Z"])
            
            
        self.x_max.hardware_read_func = lambda: self.nanopositioner.cal[self.PI_AXIS_ID["X"]-1]
        self.y_max.hardware_read_func = lambda: self.nanopositioner.cal[self.PI_AXIS_ID["Y"]-1]
        if self.nanopositioner.num_axes > 2:
            print('self.PI_AXIS_ID["Z"]', self.PI_AXIS_ID["Z"])
            self.z_max.hardware_read_func = lambda: self.nanopositioner.cal[self.PI_AXIS_ID["Z"]-1]
        
        #self.move_speed.hardware_read_func = self.nanopositioner.get_max_speed
        #self.move_speed.hardware_set_func =  self.nanopositioner.set_max_speed
        #self.move_speed.write_to_hardware()
        
        
        self.read_from_hardware()
        
        print ('Axis mapping:', ' X:', self.PI_AXIS_ID['X'], ' Y:',self.PI_AXIS_ID['Y'], ' Z:',self.PI_AXIS_ID['Z'])
        
        # Open connection to hardware
        
        
        
        
    def move_to_pt(self):
            # connect logged quantities
        self.x_target.hardware_set_func  = \
            lambda x: self.nanopositioner.set_pos_ax_slow(x, self.PI_AXIS_ID["X"])
        self.y_target.hardware_set_func  = \
            lambda y: self.nanopositioner.set_pos_ax_slow(y, self.PI_AXIS_ID["Y"])
        if self.nanopositioner.num_axes > 2:
            self.z_target.change_readonly(False)
            self.z_target.hardware_set_func  = \
                lambda z: self.nanopositioner.set_pos_ax_slow(z, self.PI_AXIS_ID["Z"])
        else:
                self.z_target.change_readonly(True)
        
        
        self.read_from_hardware()
        
        print ('Axis mapping:', ' X:', self.PI_AXIS_ID['X'], ' Y:',self.PI_AXIS_ID['Y'], ' Z:',self.PI_AXIS_ID['Z'])
    
    def move_in_vel(self):
            # connect logged quantities
        self.x_target.hardware_set_func  = None
        self.y_target.hardware_set_func  = None
        if self.nanopositioner.num_axes > 2:
            self.z_target.change_readonly(False)
            self.z_target.hardware_set_func  = None
        else:
                self.z_target.change_readonly(True)
    
    
    
    def jog(self):
        vx, vy = self.nanopositioner.set_vel_xy(self.xy_vel.value, self.x_target.value, self.y_target.value)
        z_target, vz = self.nanopositioner.z_comp(self.xz_ratio.value, self.yz_ratio.value, vx, vy, self.x_target.value, self.y_target.value)
        self.nanopositioner.jogging(self.x_target.value, self.y_target.value, z_target, vx, vy, vz)
        
        self.read_from_hardware()
    
    
    def disconnect(self):
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()

        #disconnect hardware
        if hasattr(self, 'nanopositioner'):
            self.nanopositioner.close()
            # clean up hardware object
            del self.nanopositioner
        
    @property
    def v_axis_id(self):
        return self.PI_AXIS_ID[self.v_axis.val]
    
    @property
    def h_axis_id(self):
        return self.PI_AXIS_ID[self.h_axis.val]
    
    @property
    def x_axis_id(self):
        return self.PI_AXIS_ID["X"]
    
    @property
    def y_axis_id(self):
        return self.PI_AXIS_ID["Y"]
    
    @property
    def z_axis_id(self):
        return self.PI_AXIS_ID["Z"]