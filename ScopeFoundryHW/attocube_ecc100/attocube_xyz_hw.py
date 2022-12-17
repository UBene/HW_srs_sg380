'''
Created on Jul 24, 2014


@author: Edward Barnard
'''
from __future__ import absolute_import

import time

from ScopeFoundry import HardwareComponent
from ScopeFoundry.helper_funcs import QLock, QNonReEntrantLock

try:
    from .attocube_ecc100 import AttoCubeECC100
except Exception as err:
    print("could not load modules needed for AttoCubeECC100: {}".format(err))


class AttoCubeXYZStageHW(HardwareComponent):

    name = 'attocube_xyz_stage'

    def __init__(self, app, debug=False, name=None, ax_names='xyz'):
        self.ax_names = ax_names
        #self.pro = True
        HardwareComponent.__init__(self, app, debug=debug, name=name)

    def setup(self):
        # Created logged quantities

        self.settings.New('pro_mode', dtype=bool, ro=True)

        #self.lock = QLock(mode = 0)
        self.lock = QNonReEntrantLock()
        S = self.settings

        for axis in self.ax_names:
            S.New(axis + "_position",
                              dtype=float,
                              ro=True,
                              unit='mm',
                              spinbox_decimals=6,
                              si=False
                              )

            #self.settings.New(axis + "_ref_position", dtype=float, ro=True, unit='nm')

            S.New(axis + "_target_position",
                              dtype=float,
                              ro=False,
                              vmin=-20,
                              vmax=20,
                              unit='mm',
                              spinbox_decimals=6,
                              spinbox_step=0.01,
                              si=False)

            S.New(axis + "_enable_closedloop", dtype=bool,
                              ro=False)
            S.New(axis + "_enable_output",
                              dtype=bool, initial=True)
            S.New(axis + "_electrically_connected", dtype=bool,
                              ro=True)
            S.New(axis + "_reference_found", dtype=bool,
                              ro=True)
            S.New(axis + "_reference_position", dtype=float,
                              spinbox_decimals=6, si=False,
                              unit='mm', ro=True)

            S.New(axis + "_continuous_motion",
                              dtype=int, ro=True,
                              choices=[('+ Forward', +1), ('STOP', 0), ('- Backward', -1)])

            # if self.pro:
            S.New(axis + "_auto_reference_update", dtype=bool,
                              ro=False)
            S.New(axis + "_auto_reference_reset", dtype=bool,
                              ro=False)
            S.New(axis + "_eot_stop", dtype=bool,
                              ro=False)
            S.New(axis + "_eot_forward", dtype=bool,
                              ro=True)
            S.New(axis + "_eot_back", dtype=bool, ro=True)
            # done pro

            S.New(axis + "_step_voltage",
                              dtype=float, vmin=0, vmax=45, unit='V',
                              ro=False)
            # if self.pro:
            S.New(axis + "_openloop_voltage", unit='V',
                              dtype=float, si=False, ro=False)

            S.New(axis + "_frequency", unit='Hz',
                              dtype=float, vmin=1, vmax=10000, si=False, ro=False)
            # done pro

            S.New(axis + "_actor_type", dtype=str, ro=True)
            S.New(axis + "_actor_name", dtype=str, ro=True)

            # Target Status is NCB_FeatureNotAvailable
            #self.settings.New(axis + "_target_status", dtype=bool, ro=True)

            S.New(axis + "_jog_step", dtype=float,
                              spinbox_decimals=6, si=False, unit='mm', ro=False,
                              initial=0.001)
            for sign in "pm":
                # Seems that pyqt passes a bool to func if func has arguments. ?
                def func(b, axis=axis, sign=sign): return self.move_jog_step(
                    axis=axis, sign=sign)
                self.add_operation(axis + "_jog_"+sign, func)

        S.New('device_num', int, initial=0)
        S.New('device_id', int, initial=0)
        S.New('connect_by', str, initial='device_num', choices=(
            'device_num', 'device_id'))
        #self.settings.New('axis_map', dtype=str, initial='xyz')
        # need enable boolean lq's

    def connect(self):
        if self.settings['debug_mode']:
            print("connecting to attocube_xy_stage")

        self.settings.device_num.change_readonly(True)
        self.settings.device_id.change_readonly(True)
        # self.settings.axis_map.change_readonly(True)

        # Open connection to hardware
        if self.settings['connect_by'] == 'device_num':
            self.ecc100 = AttoCubeECC100(
                device_num=self.settings['device_num'], debug=self.settings['debug_mode'])
            self.settings['device_id'] = self.ecc100.device_id
        if self.settings['connect_by'] == 'device_id':
            self.ecc100 = AttoCubeECC100(
                device_id=self.settings['device_id'], debug=self.settings['debug_mode'])
            self.settings['device_num'] = self.ecc100.device_num

        self.settings['pro_mode'] = self.ecc100.pro_version_check()

        for axis_num, axis_name in enumerate(self.ax_names):
            print(axis_num, axis_name)
            if axis_name != "_":
                # Enable Axes
                self.ecc100.enable_axis(axis_num, enable=True)

                # connect logged quantities

                self.settings.get_lq(axis_name + "_position").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_position_axis(a))

                self.settings.get_lq(axis_name + "_target_position").connect_to_hardware(
                    read_func=lambda a=axis_num: self.ecc100.read_target_position_axis(
                        a),
                    write_func=lambda new_pos, a=axis_num: self.ecc100.write_target_position_axis(a, new_pos))

                self.settings.get_lq(axis_name + "_step_voltage").connect_to_hardware(
                    read_func=lambda a=axis_num: self.ecc100.read_step_voltage(
                        a),
                    write_func=lambda volts, a=axis_num: self.ecc100.write_step_voltage(a, volts))

                self.settings.get_lq(axis_name + "_electrically_connected").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.is_electrically_connected(a))

                self.settings.get_lq(axis_name + "_reference_found").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_reference_status(a))

                self.settings.get_lq(axis_name + "_reference_position").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_reference_position(a))

                self.settings.get_lq(axis_name + "_enable_output").connect_to_hardware(
                    read_func=lambda a=axis_num: self.ecc100.read_enable_axis(
                        a),
                    write_func=lambda enable, a=axis_num: self.ecc100.enable_axis(a, enable))

                self.settings.get_lq(axis_name + "_enable_closedloop").connect_to_hardware(
                    read_func=lambda a=axis_num: self.ecc100.read_enable_closedloop_axis(
                        a),
                    write_func=lambda enable, a=axis_num: self.ecc100.enable_closedloop_axis(
                        a, enable)
                )

                self.settings.get_lq(axis_name + "_continuous_motion").connect_to_hardware(
                    read_func=lambda a=axis_num: self.ecc100.read_continuous_motion(
                        a),
                    write_func=lambda dir, a=axis_num: self.ecc100.start_continuous_motion(
                        a, dir)
                )

                # Target Status is NCB_FeatureNotAvailable
                # self.settings.get_lq(axis_name + "_target_status").connect_to_hardware(
                #    read_func = lambda a=axis_num: self.ecc100.read_target_status(a)
                #    )

                if self.settings['pro_mode']:
                    #                     self.x_openloop_voltage.hardware_read_func = lambda: self.ecc100.read_openloop_voltage(X_AXIS)
                    #                     self.x_openloop_voltage.hardware_set_func = lambda x: self.ecc100.write_openloop_voltage(X_AXIS, x)

                    self.settings.get_lq(axis_name + "_eot_stop").connect_to_hardware(
                        read_func=lambda a=axis_num: self.ecc100.read_enable_eot_stop(
                            a),
                        write_func=lambda enable, a=axis_num: self.ecc100.enable_eot_stop(a, enable))
                    self.settings.get_lq(axis_name + "_eot_forward").connect_to_hardware(
                        lambda a=axis_num: self.ecc100.read_eot_forward_status(a))
                    self.settings.get_lq(axis_name + "_eot_back").connect_to_hardware(
                        lambda a=axis_num: self.ecc100.read_eot_back_status(a))
                    self.settings.get_lq(axis_name + "_frequency").connect_to_hardware(
                        read_func=lambda a=axis_num: self.ecc100.read_frequency(
                            a),
                        write_func=lambda freq, a=axis_num: self.ecc100.write_frequency(a, freq))
                    self.settings.get_lq(axis_name + "_auto_reference_update").connect_to_hardware(
                        read_func=lambda a=axis_num: self.ecc100.read_enable_auto_update_reference(
                            a),
                        write_func=lambda enable, a=axis_num: self.ecc100.enable_auto_update_reference(a, enable))
                    self.settings.get_lq(axis_name + "_auto_reference_reset").connect_to_hardware(
                        read_func=lambda a=axis_num: self.ecc100.read_enable_auto_reset_reference(
                            a),
                        write_func=lambda enable, a=axis_num: self.ecc100.enable_auto_reset_reference(a, enable))

                self.settings.get_lq(axis_name + "_actor_type").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_actor_type(a))
                self.settings.get_lq(axis_name + "_actor_name").connect_to_hardware(
                    lambda a=axis_num: self.ecc100.read_actor_name(a))

        self.read_from_hardware()

        # update units based on Actor type
        for axis_num, axis_name in enumerate(self.ax_names):
            if axis_name != "_":
                actor_type = self.settings[axis_name + "_actor_type"]
                if actor_type == 'ECC_actorLinear':
                    self.settings.get_lq(
                        axis_name + "_position").change_unit("mm")
                    self.settings.get_lq(
                        axis_name + "_target_position").change_unit("mm")
                elif actor_type in ['ECC_actorGonio', 'ECC_actorRot']:
                    self.settings.get_lq(
                        axis_name + "_position").change_unit("deg")
                    self.settings.get_lq(
                        axis_name + "_target_position").change_unit("deg")

        # find axes with step voltage too small due to weird firmware issues
        for axis_num, axis_name in enumerate(self.ax_names):
            if axis_name != "_":
                step_volt = self.settings.get_lq(axis_name + "_step_voltage")
                if step_volt.val < 5:
                    step_volt.update_value(30)
                step_freq = self.settings.get_lq(axis_name + "_frequency")
                if step_freq.val < 5:
                    step_freq.update_value(1000)

    def disconnect(self):

        self.settings.device_num.change_readonly(False)
        self.settings.device_id.change_readonly(False)
        # self.settings.axis_map.change_readonly(False)

        # disconnect logged quantities from device
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None

        if hasattr(self, 'ecc100'):
            # disconnect device
            self.ecc100.close()

            # clean up device object
            del self.ecc100

    def reset_axis_by_name(self, ax_name):
        assert ax_name in self.ax_names

        for i, ax in enumerate(self.ax_names):
            if ax_name == ax:
                self.ecc100.reset_axis(i)

    def home_and_wait(self, axis_name, safe_travel_dir):
        print("home_and_wait", self.name, axis_name, safe_travel_dir)
        home_meas = self.app.measurements['attocube_home_axis']
        home_meas.settings['hw_name'] = self.name
        home_meas.settings['axis_name'] = axis_name
        home_meas.settings['safe_travel_dir'] = safe_travel_dir

        # run home_meas, wait for completion
        home_meas.start()

        while home_meas.is_measuring():
            time.sleep(0.001)
        # check to verify homing
        return self.settings[axis_name + "_reference_found"]

    def move_and_wait(self, axis_name, new_pos, target_range=50e-3, timeout=15):
        print("move_and_wait", self.name, axis_name, new_pos)

        hw = self
        hw.settings[axis_name + "_target_position"] = new_pos

        t0 = time.time()

        # Wait until stage has moved to target
        while True:
            pos = hw.settings.get_lq(
                axis_name + "_position").read_from_hardware()
            distance_from_target = abs(pos - new_pos)
            if distance_from_target < target_range:
                #print("settle time {}".format(time.time() - t0))
                break
            if (time.time() - t0) > timeout:
                raise IOError(
                    "AttoCube ECC100 took too long to reach position")
            time.sleep(0.005)

    def single_step(self, ax_name, direction):
        """direction True (or >0): forward, False (or <=0): backward"""

        assert ax_name in self.ax_names

        for i, ax in enumerate(self.ax_names):
            if ax_name == ax:
                self.ecc100.single_step(i, direction)

    def move_jog_step(self, axis, sign):
        S = self.settings
        delta = {"p": 1.0, "m": -1.0}[sign] * S[axis + "_jog_step"]
        print(axis, delta)
        S[axis + "_target_position"] += delta
