'''
Created on Jul 27, 2014

@author: Edward Barnard
'''
from ScopeFoundry import HardwareComponent
from ScopeFoundryHW.pi_xyz_stage.pi_nanopositioner_usingwaiton import PINanopositioner
# from ScopeFoundryHW.pi_xyz_stage.pi_nanopositioner import PINanopositioner
from qtpy import QtCore


class PIXYZStageHW(HardwareComponent):
    
    name = 'PI_xyz_stage'
    
    def setup(self):
        S = self.settings
        lq_params = dict(dtype=float, ro=True,
                           initial=1,
                           spinbox_decimals=3,
                           vmin=-1,
                           vmax=190,
                           si=False,
                           unit='um')
        self.x_position = S.New("x_position", **lq_params)
        self.y_position = S.New("y_position", **lq_params)       
        self.z_position = S.New("z_position", **lq_params)
        
        lq_params = dict(dtype=float, ro=False,
                           initial=50,
                           spinbox_decimals=3,
                           vmin=0,
                           vmax=200,
                           unit='um')
        self.x_target = S.New("x_target", **lq_params)
        self.y_target = S.New("y_target", **lq_params)       
        self.z_target = S.New("z_target", **lq_params)        
        
        lq_params = dict(unit="um", dtype=float, ro=True, initial=200,
                         spinbox_decimals=3,
                         si=False)
        self.x_max = S.New("x_max", **lq_params)
        self.y_max = S.New("y_max", **lq_params)
        self.z_max = S.New("z_max", **lq_params)

        lq_params = dict(dtype=str, choices=[("X", "X"), ("Y", "Y"), ("Z", "Z")])
        self.h_axis = S.New("h_axis", initial="X", **lq_params)
        self.v_axis = S.New("v_axis", initial="Y", **lq_params)
        
        
        S.New('controller_name', str, initial='E-727')
        
        # ##Is this working?
        self.PI_AXIS_ID = dict(X=1, Y=2, Z=3)
        self.xyz_axis_map = S.New('xyz_axis_map', dtype=str, initial='123')
        self.xyz_axis_map.updated_value.connect(self.on_update_xyz_axis_map)
        
        # self.move_speed = self.add_logged_quantity(name='move_speed',
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
    
    def move_pos_slow(self, x=None, y=None, z=None):
        # move slowly to new position
        new_pos = [None, None, None]
        new_pos[self.PI_AXIS_ID['X'] - 1] = x
        new_pos[self.PI_AXIS_ID['Y'] - 1] = y
        new_pos[self.PI_AXIS_ID['Z'] - 1] = z
        if self.nanopositioner.num_axes < 3:
            new_pos[2] = None
        self.nanopositioner.set_pos_slow(*new_pos)

        # self.read_pos()
        
    def move_pos_fast(self, x=None, y=None, z=None):
        new_pos = [None, None, None]
        new_pos[self.PI_AXIS_ID['X'] - 1] = x
        new_pos[self.PI_AXIS_ID['Y'] - 1] = y
        new_pos[self.PI_AXIS_ID['Z'] - 1] = z
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
        if self.debug_mode.val: print("connecting", self.name)


        S = self.settings
        
        # Open connection to hardware
        
        deviceaxes = [x for x in S['xyz_axis_map']]
        self.nanopositioner = PINanopositioner(debug=S['debug_mode'], 
                                               CONTROLLERNAME=S['controller_name'], 
                                               deviceaxes=deviceaxes)
        
        # connect logged quantities
        self.x_target.hardware_set_func = \
            lambda x: self.nanopositioner.set_pos_ax_slow(x, self.PI_AXIS_ID["X"])
        self.y_target.hardware_set_func = \
            lambda y: self.nanopositioner.set_pos_ax_slow(y, self.PI_AXIS_ID["Y"])
        if self.nanopositioner.num_axes > 2:
            self.z_target.change_readonly(False)
            self.z_target.hardware_set_func = \
                lambda z: self.nanopositioner.set_pos_ax_slow(z, self.PI_AXIS_ID["Z"])
        else:
            self.z_target.change_readonly(True)
        
        self.x_position.hardware_read_func = \
            lambda: self.nanopositioner.get_pos_ax(int(self.PI_AXIS_ID["X"]))
        self.y_position.hardware_read_func = \
            lambda: self.nanopositioner.get_pos_ax(int(self.PI_AXIS_ID["Y"]))
        if self.nanopositioner.num_axes > 2:
            self.z_position.hardware_read_func = \
                lambda: self.nanopositioner.get_pos_ax(self.PI_AXIS_ID["Z"])
        
        self.x_max.hardware_read_func = lambda: self.nanopositioner.cal[self.PI_AXIS_ID["X"]]
        self.y_max.hardware_read_func = lambda: self.nanopositioner.cal[self.PI_AXIS_ID["Y"]]
        if self.nanopositioner.num_axes > 2:
            self.z_max.hardware_read_func = lambda: self.nanopositioner.cal[self.PI_AXIS_ID["Z"]]
            # print("self.PI_AXIS_ID["Z"], self.PI_AXIS_ID["Z"])
            # print("self.nanopositioner", self.nanopositioner.cal)
        # self.move_speed.hardware_read_func = self.nanopositioner.get_max_speed
        # self.move_speed.hardware_set_func =  self.nanopositioner.set_max_speed
        # self.move_speed.write_to_hardware()
        
        self.read_from_hardware()
        
        print ('Axis mapping:', ' X:', self.PI_AXIS_ID['X'], ' Y:', self.PI_AXIS_ID['Y'], ' Z:', self.PI_AXIS_ID['Z'])

    def disconnect(self):
        # disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()

        # disconnect hardware
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
