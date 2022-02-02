from ScopeFoundry.hardware import HardwareComponent
from .thorlabs_stepper_controller_dev import ThorlabsStepperControllerDev
from qtpy import  QtCore
import time
from collections import OrderedDict

class ThorlabsStepperControllerHW(HardwareComponent):
    
    name = "thorlabs_stepper_controller"
    
    
    def __init__(self, app,debug=False, name=None, ax_names='xyz'):
        self.ax_names = ax_names
        self.ax_dict = OrderedDict() # dictionary ax_name: ax_num
        for axis_index, axis_name in enumerate(self.ax_names):
            axis_num = axis_index +1
            # skip hidden axes
            if not axis_name or axis_name == "_" or axis_name is None:
                continue
            self.ax_dict[axis_name] = axis_num
            
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):
        
        
        for axis in self.ax_dict.keys():
            
            self.settings.New(axis + "_enable", dtype=bool, initial=True)
            
            self.settings.New(axis + "_position", 
                               dtype=float,
                               ro=True,
                               unit='mm',
                               spinbox_decimals=6,
                               si=False
                               )
            
            
            self.settings.New(axis + "_target_position",
                                dtype=float,
                                ro=False,
                                vmin=-20,
                                vmax=20,
                                unit='mm',
                                spinbox_decimals=6,
                                spinbox_step=0.01,
                                si=False)

            self.settings.New(axis + "_velocity", dtype=float,
                              unit='mm/s', 
                              initial=1.0,
                              spinbox_decimals=6)
            self.settings.New(axis + "_acceleration", dtype=float,
                              unit='mm/s^2', 
                              initial=1.0,
                              spinbox_decimals=6,)

            self.settings.New(axis +"_step_convert", dtype=float, 
                              spinbox_decimals=0, unit="step/mm", initial=34133)
            
            print("setup", axis)
            self.add_operation("Home_Axis_" + axis, lambda a=axis: self.home_axis(a))
            
            
            
        
        self.settings.New('device_num', dtype=int, initial=0)
        self.settings.New('serial_num', dtype=str, initial="")

        self.add_operation('Stop_Motion', self.stop_all_axes)
        


    def connect(self):
        S = self.settings
        
        self.dev = ThorlabsStepperControllerDev(
                        dev_num=S['device_num'],
                        serial_num=S['serial_num'],
                        debug=S['debug_mode'])
        
        

        for axis_name, axis_num in self.ax_dict.items():
            
            scale = self.settings[axis_name + "_step_convert"] # step/mm
            
            en = self.settings.get_lq(axis_name + "_enable")
            en.connect_to_hardware(
                write_func = lambda enable, a=axis_num: 
                                self.dev.write_chan_enable(a, enable))
            en.write_to_hardware()
            
            self.settings.get_lq(axis_name + "_position").connect_to_hardware(
                lambda a=axis_num, scale=scale: 
                    self.dev.read_position(a) / scale)
    
            self.settings.get_lq(axis_name + "_target_position").connect_to_hardware(
                write_func = lambda new_pos, a=axis_num, scale=scale: 
                                self.dev.write_move_to_position(a, int(round(scale*new_pos))))

            vel = self.settings.get_lq(axis_name + "_velocity")
            vel.connect_to_hardware(
                read_func = lambda a=axis_num, scale=scale: self.dev.read_velocity(a)/scale,
                write_func = lambda vel, ax_name=axis_name: self.write_velocity_params(ax_name, vel=vel)
                )
            
            #vel.write_to_hardware()
            
            acc = self.settings.get_lq(axis_name + "_acceleration")
            acc.connect_to_hardware(
                read_func = lambda a=axis_num, scale=scale: self.dev.read_acceleration(a)/scale,
                write_func = lambda acc, ax_name=axis_name: self.write_velocity_params(ax_name, acc=acc)
                )
            #acc.write_to_hardware()

            


        #time.sleep(1)
        self.read_from_hardware()
        
        S['serial_num'] = self.dev.get_serial_num()

        self.display_update_timer = QtCore.QTimer(self)
        self.display_update_timer.timeout.connect(self.on_display_update_timer)
        self.display_update_timer.start(200) # 200ms
        
    def write_velocity_params(self, ax_name, acc=None, vel=None):
        #takes units of mm
        ax_num  = self.ax_dict[ax_name]
        if acc is None:
            acc = self.settings[ax_name + "_acceleration"]
        if vel is None:
            vel = self.settings[ax_name + "_velocity"]
            
        scale = self.settings[ax_name + "_step_convert"] # step/mm
        self.dev.write_velocity_params(ax_num, int(round(scale*acc)), int(round(scale*vel)))
        self.dev.write_homing_velocity(ax_num, int(round(scale*vel)))
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, "display_update_timer"):
            self.display_update_timer.stop()
            del self.display_update_timer
        
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
        
        
    def home_axis(self, ax_name):
        print("home_axis", ax_name)
        self.dev.start_home(self.ax_dict[ax_name])
    
    def stop_axis(self, ax_name):
        pass
    
    def stop_all_axes(self):
        for axis_name, axis_num in self.ax_dict.items():
            self.dev.stop_profiled(chan=axis_num)

    
    def on_display_update_timer(self):
        self.read_position_from_hardware()
        
    def read_position_from_hardware(self):
        for axis_name, axis_num in self.ax_dict.items():
            self.settings.get_lq(axis_name + "_position").read_from_hardware()
            
    
    def read_message_queue(self,ax_name):
        return self.dev.read_message_queue(self.ax_dict[ax_name])
            
