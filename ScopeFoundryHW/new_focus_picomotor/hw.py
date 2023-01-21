'''
Created on Jan 20, 2023

@author: Benedikt Ursprung
'''

from ScopeFoundry.hardware import HardwareComponent
from qtpy import QtCore, QtWidgets
from functools import partial


class HW(HardwareComponent):

    name = "picomotor"

    def setup(self):

        position_kwargs = {"dtype": int,
                           #"unit": "",
                           'si': False,
                           #"spinbox_decimals":6
                           }

        for axis in range(1, 5):

            self.settings.New(f"{axis}_position",
                              ro=True,
                              **position_kwargs,
                              )
            self.settings.New(f"{axis}_target_position",
                              ro=False,
                              **position_kwargs,
                              )
            self.settings.New(f"{axis}_is_moving",
                              bool,
                              initial=False,
                              ro=True)

            self.add_operation(f'{axis} jog +',
                               partial(self.jog_forward, axis=axis))
            self.add_operation(f'{axis} jog -', partial(
                self.jog_backward, axis=axis))

        self.settings.New("jog_size", 
                          initial=100,
                          **position_kwargs)

        # self.settings.New("velocity", dtype=float,
        #                   unit='mm/s',
        #                   initial=1.0,
        #                   spinbox_decimals=6)

        # self.settings.New("acceleration", dtype=float,
        #                   unit='mm/s^2',
        #                   initial=1.0,
        #                   spinbox_decimals=6,)
        # self.settings.New("step_convert",
        #                   dtype=float,
        #                   spinbox_decimals=0,
        #                   unit="step/mm",
        #                   initial=863874 / 25.0)

        self.settings.New('device_num', int, initial=0)
        self.settings.New('idn', str, initial="", ro=False)
        self.add_operation('stop', self.write_abort_motion)

    def connect(self):
        S = self.settings
        from .dev import Dev
        self.dev = Dev(S['device_num'], S['debug_mode'])

        for axis in range(1, 5):

            S.get_lq(f"{axis}_position").connect_to_hardware(
                partial(self.dev.read_position, axis=axis)
            )
            S.get_lq(f"{axis}_target_position").connect_to_hardware(
                partial(self.dev.read_target_position, axis=axis),
                partial(self.dev.write_target_position, axis=axis)
            )
            S.get_lq(f'{axis}_is_moving').connect_to_hardware(
                partial(self.dev.read_is_in_motion, axis=axis))

        S.get_lq('device_num').connect_to_hardware(None, self.set_device_num)
        self.settings['idn'] = self.dev.read_identification()

        self.read_from_hardware()

        self.display_update_timer = QtCore.QTimer(self)
        self.display_update_timer.timeout.connect(self.on_display_update_timer)
        self.display_update_timer.start(200)  # 200ms

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()

        if hasattr(self, "display_update_timer"):
            self.display_update_timer.stop()
            del self.display_update_timer

        if hasattr(self, 'dev'):
            self.settings['idn'] = ""
            self.dev.close()
            del self.dev

    def jog_forward(self, axis):
        self.dev.write_move_relative(self.settings['jog_size'], axis)

    def jog_backward(self, axis):
        self.dev.write_move_relative(-self.settings['jog_size'], axis)

    def write_abort_motion(self):
        self.dev.write_abort_motion()

    # def read_position(self):
    #     return self.dev.read_position() / self.settings['step_convert']
    #
    # def write_target_position(self, position):
    #     index = int(position * self.settings['step_convert'])
    #     self.dev.write_move_to_position(index)

    def set_device_num(self, num):
        self.dev.set_device_num(num)
        self.settings['idn'] = self.dev.read_identification()

    def on_display_update_timer(self):
        for axis in range(1, 5):
            self.settings.get_lq(f"{axis}_position").read_from_hardware()
            self.settings.get_lq(f"{axis}_is_moving").read_from_hardware()

    def New_quick_UI(self, axes=(1, 2, 3, 4)):
        S = self.settings
        widget = QtWidgets.QGroupBox(title=self.name)
        main_layout = QtWidgets.QVBoxLayout(widget)
        main_layout.addWidget(self.settings.New_UI(('connected', 'jog_size')))
        h_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(h_layout)
        for axis in axes:
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(S.get_lq(f"{axis}_position").new_default_widget())
            layout.addWidget(
                S.get_lq(f"{axis}_target_position").new_default_widget())
            for sign in ('+', '-'):
                name = f'{axis} jog {sign}'
                btn = QtWidgets.QPushButton(name)
                btn.clicked.connect(self.operations[name])
                layout.addWidget(btn)
            h_layout.addLayout(layout)
        widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                             QtWidgets.QSizePolicy.Maximum)
        return widget
