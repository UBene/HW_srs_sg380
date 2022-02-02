from ScopeFoundry import HardwareComponent
from ScopeFoundry.helper_funcs import QLock
from ScopeFoundryHW.attocube_amc100.AMC100_Python import AMC
import time

class AttoCubeAMC100StageHW(HardwareComponent):
    
    name = "attocube_amc100"
    
    def __init__(self, app, debug=False, name=None, ax_names='xyz'):
        self.ax_names = ax_names
        #self.pro = True        
        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        # Created logged quantities
        
        self.settings.New('pro_mode', dtype=bool, ro=True)

        self.lock = QLock(mode=0) # nonre-entrant
        
        for axis in self.ax_names:
            # Skip axis if disable in __init__ ax_names
            if axis == '_':
                continue
            
            self.settings.New(axis + "_position", 
                               dtype=float,
                               ro=True,
                               unit='mm',
                               spinbox_decimals=6,
                               si=False
                               )
            
            #self.settings.New(axis + "_ref_position", dtype=float, ro=True, unit='nm')
            
            self.settings.New(axis + "_target_position",
                                dtype=float,
                                ro=False,
                                vmin=-20,
                                vmax=20,
                                unit='mm',
                                spinbox_decimals=6,
                                spinbox_step=0.01,
                                si=False)
        
            self.settings.New(axis + "_enable_closedloop", dtype=bool,
                                                                 ro=False)
            self.settings.New(axis + "_enable_output", dtype=bool, initial=True)
            self.settings.New(axis + "_electrically_connected", dtype=bool,
                                                               ro=True)
            self.settings.New(axis + "_reference_found", dtype=bool,
                                                               ro=True)
            self.settings.New(axis + "_reference_position", dtype=float,
                                spinbox_decimals=6, si = False,
                              unit='mm', ro=True)
           
            self.settings.New(axis + "_continuous_motion", 
                              dtype=int, ro=True, 
                              choices=[('+ Forward',+1), ('STOP',0), ('- Backward', -1)])
           
            #if self.pro:
            self.settings.New(axis + "_auto_reference_update", dtype=bool,
                                                           ro=False)
            self.settings.New(axis + "_auto_reference_reset", dtype=bool,
                                                           ro=False)
            self.settings.New(axis + "_eot_stop", dtype=bool,
                                                           ro=False)
            self.settings.New(axis + "_eot_forward", dtype=bool,
                                                           ro=True)
            self.settings.New(axis + "_eot_back", dtype=bool, ro=True)
            # done pro
       
            self.settings.New(axis + "_step_voltage",
                                dtype=float, vmin=0, vmax = 45, unit='V',
                                ro=False)
            #if self.pro:
            self.settings.New(axis + "_openloop_voltage", unit = 'V',
                                    dtype=float, si=False, ro=False)
        
        
            self.settings.New(axis + "_frequency", unit = 'Hz',
                                    dtype=float, vmin = 1, vmax = 10000, si=False, ro=False)
            # done pro
                
            self.settings.New(axis + "_actor_type", dtype=str, ro=True)
            self.settings.New(axis + "_actor_name", dtype=str, ro=True)
        
            
            # Target Status is NCB_FeatureNotAvailable
            #self.settings.New(axis + "_target_status", dtype=bool, ro=True)

        self.settings.New('ip_address', dtype=str, initial='192.168.1.105')
            
            
    def connect(self):
        if self.settings['debug_mode']: print("connecting to attocube AMC100")
        
        self.settings.ip_address.change_readonly(True)

        self.amc = AMC.Device(self.settings['ip_address'])
        
        self.amc.connect()
        
        #self.settings['pro_mode'] = self.amc.pro_version_check()
        
        for axis_num, axis_name in enumerate(self.ax_names):
            print(axis_num, axis_name)
            if axis_name != "_":
                # Enable Axes
                # ECC_controlOutput
                self.amc.control.setControlOutput(axis_num,enable=True)
                

                # connect logged quantities
                
                self.settings.get_lq(axis_name + "_position").connect_to_hardware(
                    lambda a=axis_num: self.amc.move.getPosition(a))
        
                self.settings.get_lq(axis_name + "_target_position").connect_to_hardware(
                    read_func = lambda a=axis_num: self.amc.control.getControlTargetPosition(a)[1],
                    write_func = lambda new_pos, a=axis_num: self.amc.control.setControlTargetPosition(a, new_pos))
                
                self.settings.get_lq(axis_name + "_step_voltage").connect_to_hardware(
                    read_func = lambda a=axis_num: self.amc.control.getControlAmplitudeInV(a)[1],
                    write_func = lambda volts, a=axis_num: self.amc.control.setControlAmplitude(a,volts))
                    
                self.settings.get_lq(axis_name + "_electrically_connected").connect_to_hardware(
                    lambda a=axis_num: self.amc.status.getStatusConnected(a))
                
                self.settings.get_lq(axis_name + "_reference_found").connect_to_hardware(
                    lambda a=axis_num: self.amc.status.getStatusReference(a)[1])

                self.settings.get_lq(axis_name + "_reference_position").connect_to_hardware(
                    lambda a=axis_num: self.amc.control.getReferencePositionInmm(a)[1])
                
                self.settings.get_lq(axis_name + "_enable_output").connect_to_hardware(
                    read_func  = lambda a=axis_num: self.amc.getControlOutput(a)[1],
                    write_func = lambda enable, a=axis_num: self.amc.control.setControlOutput(a, enable))
                    
                self.settings.get_lq(axis_name + "_enable_closedloop").connect_to_hardware(
                    read_func = lambda a=axis_num: self.amc.control.getControlMove(a)[1],
                    write_func = lambda enable, a=axis_num: self.amc.control.setControlMove(a, enable)
                    )
                
                #FIXME
#                 self.settings.get_lq(axis_name + "_continuous_motion").connect_to_hardware(
#                     read_func = lambda a=axis_num: self.ecc100.(a),
#                     write_func = lambda dir, a=axis_num: self.ecc100.start_continuous_motion(a, dir)
#                     )
                                    
                # Target Status is NCB_FeatureNotAvailable
                #self.settings.get_lq(axis_name + "_target_status").connect_to_hardware(
                #    read_func = lambda a=axis_num: self.ecc100.read_target_status(a) 
                #    )

                #if self.settings['pro_mode']:
                if True:
#                     self.x_openloop_voltage.hardware_read_func = lambda: self.ecc100.read_openloop_voltage(X_AXIS)
#                     self.x_openloop_voltage.hardware_set_func = lambda x: self.ecc100.write_openloop_voltage(X_AXIS, x)
                                    
                    self.settings.get_lq(axis_name + "_eot_stop").connect_to_hardware(
                        read_func = lambda a=axis_num: self.amc.control.getControlEotOutputDeactive(a)[1],
                        write_func = lambda enable, a=axis_num: self.amc.control.setControlEotOutputDeactive(a,enable))
                    self.settings.get_lq(axis_name + "_eot_forward").connect_to_hardware(
                        lambda a=axis_num: self.amc.status.getStatusEotFwd(a)[1])
                    self.settings.get_lq(axis_name + "_eot_back").connect_to_hardware(
                        lambda a=axis_num: self.amc.status.getStatusEotBkwd(a)[1])
                    self.settings.get_lq(axis_name + "_frequency").connect_to_hardware(
                        read_func = lambda a=axis_num: self.amc.control.getControlFrequencyinHz(a)[1],
                        write_func = lambda freq, a=axis_num: self.amc.control.setControlFrequencyinHz(a,freq))
                    self.settings.get_lq(axis_name + "_auto_reference_update").connect_to_hardware(
                        read_func = lambda a=axis_num: self.amc.control.getControlReferenceAutoUpdate(a)[1],
                        write_func = lambda enable, a=axis_num: self.amc.control.setControlReferenceAutoUpdate(a,enable))
                    self.settings.get_lq(axis_name + "_auto_reference_reset").connect_to_hardware(
                        read_func = lambda a=axis_num: self.amc.control.getControlAutoReset(a)[1],
                        write_func = lambda enable, a=axis_num: self.amc.control.setControlAutoReset(a,enable))
                        
                self.settings.get_lq(axis_name + "_actor_type").connect_to_hardware(
                    lambda a=axis_num: self.amc.control.getActorType(a)[1])
                self.settings.get_lq(axis_name + "_actor_name").connect_to_hardware(
                    lambda a=axis_num: self.amc.control.getActorName(a)[1])

        self.read_from_hardware()

# TODO
#         # update units based on Actor type
#         for axis_num, axis_name in enumerate(self.ax_names):
#             if axis_name != "_":
#                 actor_type = self.settings[axis_name + "_actor_type"]
#                 if actor_type == 'ECC_actorLinear':
#                     self.settings.get_lq(axis_name + "_position").change_unit("mm")
#                     self.settings.get_lq(axis_name + "_target_position").change_unit("mm")
#                 elif actor_type in ['ECC_actorGonio', 'ECC_actorRot']:
#                     self.settings.get_lq(axis_name + "_position").change_unit("deg")
#                     self.settings.get_lq(axis_name + "_target_position").change_unit("deg")
#                     
#         # find axes with step voltage too small due to weird firmware issues
#         for axis_num, axis_name in enumerate(self.ax_names):
#             if axis_name != "_":
#                 step_volt = self.settings.get_lq(axis_name + "_step_voltage")
#                 if step_volt.val < 5:
#                     step_volt.update_value(30)
#                 step_freq = self.settings.get_lq(axis_name + "_frequency")
#                 if step_freq.val < 5:
#                     step_freq.update_value(1000)
                

    def disconnect(self):
        
        self.settings.ip_address.change_readonly(False)

        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'amc'):
            self.amc.close()
            
            del self.amc
    
    def reset_axis_by_name(self, ax_name):
        """
        This function resets the actual position of the selected axis to zero
        and marks the reference position as invalid.
        
        takes an axis name
        """
        assert ax_name in self.ax_names
        
        for i, ax in enumerate(self.ax_names):
            if ax_name == ax:
                self.amc.control.setReset(i)
                
                
    def home_and_wait(self, axis_name, safe_travel_dir):
        print("home_and_wait", self.name, axis_name, safe_travel_dir)
        home_meas = self.app.measurements['attocube_home_axis']
        home_meas.settings['hw_name'] = self.name
        home_meas.settings['axis_name'] = axis_name
        home_meas.settings['safe_travel_dir'] = safe_travel_dir
        
        ## run home_meas, wait for completion
        home_meas.start()
        
        while home_meas.is_measuring():
            time.sleep(0.001)
        #check to verify homing
        return self.settings[axis_name + "_reference_found"]


    def move_and_wait(self, axis_name, new_pos, target_range=50e-3, timeout=15):
        print("move_and_wait", self.name, axis_name, new_pos)
        
        hw = self
        hw.settings[axis_name + "_target_position"] = new_pos
        
        t0 = time.time()
        
        # Wait until stage has moved to target
        while True:
            pos = hw.settings.get_lq(axis_name + "_position").read_from_hardware()
            distance_from_target = abs(pos - new_pos)
            if distance_from_target < target_range:
                #print("settle time {}".format(time.time() - t0))
                break
            if (time.time() - t0) > timeout:
                raise IOError("AttoCube AMC00 took too long to reach position")
            time.sleep(0.005)
            
            
    def single_step(self, ax_name, direction):
        """direction True (or >0): forward, False (or <=0): backward"""
            
        # TODO Need to check if direction is correct
        # Note that documentation says  true: movement in backward direction
        # which is why direction is negated
        backward= (direction <= 0)

        assert ax_name in self.ax_names
        
        for i, ax in enumerate(self.ax_names):
            if ax_name == ax:
                self.amc.move.setNSteps(i, backward, 1)
                
    def start_continuous_motion(self, axis_num, direction):
        """
        + 1 continuous motion start in Forward (+) direction
        - 1 continuous motion start in Backward (-) direction
        0   stop continuous motion
        
        """
        if direction > 0:
            with self.lock:
                self.amc.control.setControlContinuousFwd(axis_num, enable=True)
        elif direction < 0:
            with self.lock:
                self.amc.control.setControlContinuousBkwd(axis_num, enable=True)
        else:
            self.stop_continous_motion(axis_num)

    def stop_continous_motion(self, axis_num):
        with self.lock:
            self.amc.control.setControlContinuousFwd(axis_num, enable=False)
        