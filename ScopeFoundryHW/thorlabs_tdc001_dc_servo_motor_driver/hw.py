from ScopeFoundry.hardware import HardwareComponent
from qtpy import QtCore


class TDC001DCServoHW(HardwareComponent):

    name = "thorlabs_dc_servo"

    def setup(self):

        # self.settings.New("enable", dtype=bool, initial=True)

        self.settings.New("position",
                          dtype=float,
                          ro=True,
                          unit='mm',
                          spinbox_decimals=6,
                          si=False
                          )

        self.settings.New("target_position",
                          dtype=float,
                          ro=False,
                          vmin=-20,
                          vmax=25.0,
                          unit='mm',
                          spinbox_decimals=6,
                          spinbox_step=0.01,
                          si=False)
        self.settings.New("jog_size",
                          initial=0.5,
                          dtype=float,
                          ro=False,
                          vmin=0,
                          vmax=25.0,
                          unit='mm',
                          spinbox_decimals=6,
                          spinbox_step=0.01,
                          si=False)

        # self.settings.New("velocity", dtype=float,
        #                   unit='mm/s',
        #                   initial=1.0,
        #                   spinbox_decimals=6)

        # self.settings.New("acceleration", dtype=float,
        #                   unit='mm/s^2',
        #                   initial=1.0,
        #                   spinbox_decimals=6,)

        self.settings.New("step_convert",
                          dtype=float,
                          spinbox_decimals=0,
                          unit="step/mm",
                          initial=863874 / 25.0)
        self.settings.New("is_moving", bool, initial=False, ro=True)
        self.settings.New("is_homed", bool, initial=False, ro=True)
        self.settings.New("is_homing", bool, initial=False, ro=True)
        self.settings.New("is_active", bool, initial=False, ro=True)

        self.settings.New('device_num', int, initial=0)
        self.settings.New('serial_num', str, initial="")
        self.settings.New('kinesis_path',
                          str,
                          initial=r"C:\Program Files\Thorlabs\Kinesis")

        self.add_operation("home", self.home_axis)
        self.add_operation('stop', self.stop_profiled)
        self.add_operation('jog forward', self.jog_forward)
        self.add_operation('jog backward', self.stop_backward)

    def connect(self):
        S = self.settings

        from ScopeFoundryHW.thorlabs_tdc001_dc_servo_motor_driver.dev import TDC001DCServoDev

        self.dev = TDC001DCServoDev(
            kinesis_path=S['kinesis_path'],
            serial_num=S['serial_num'],
            debug=S['debug_mode'])

        S.position.connect_to_hardware(self.read_position)
        S.target_position.connect_to_hardware(None, self.write_target_position)
        S.jog_size.connect_to_hardware(self.read_jog_size, self.write_jog_size)
        S.target_position.connect_to_hardware(None, self.write_target_position)
        S.get_lq('is_moving').connect_to_hardware(self.dev.is_moving)
        S.get_lq('is_homed').connect_to_hardware(self.dev.is_homed)
        S.get_lq('is_homing').connect_to_hardware(self.dev.is_homing)
        S.get_lq('is_active').connect_to_hardware(self.dev.is_active)

        self.read_from_hardware()

        S['serial_num'] = self.dev.serial_num_in_use()

        self.display_update_timer = QtCore.QTimer(self)
        self.display_update_timer.timeout.connect(self.on_display_update_timer)
        self.display_update_timer.start(200)  # in ms

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()

        if hasattr(self, "display_update_timer"):
            self.display_update_timer.stop()
            del self.display_update_timer

        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

    def home_axis(self):
        print("home_axis")
        self.dev.start_home()

    def stop_profiled(self):
        self.dev.stop_profiled()

    def read_position(self):
        return self.dev.read_position() / self.settings['step_convert']

    def write_target_position(self, position):
        index = int(position * self.settings['step_convert'])
        self.dev.write_move_to_position(index)

    def on_display_update_timer(self):
        self.dev.update_status_bits()
        for name in ('is_homed',
                     'is_homing',
                     'is_moving',
                     'position'):
            self.settings.get_lq(name).read_from_hardware()

    def jog_forward(self):
        self.dev.jog(True)

    def stop_backward(self):
        self.dev.jog(False)

    def read_jog_size(self):
        return self.dev.read_jog_step_size() / self.settings['step_convert']

    def write_jog_size(self, size):
        index = int(size * self.settings['step_convert'])
        self.dev.write_jog_step_size(index)

    # def read_message_queue(self, ax_name):
    #     return self.dev.read_message_queue(self.ax_dict[ax_name])
    #
    # def write_velocity_params(self, ax_name, acc=None, vel=None):
    #     # takes units of mm
    #     ax_num = self.ax_dict[ax_name]
    #     if acc is None:
    #         acc = self.settings[ax_name + "_acceleration"]
    #     if vel is None:
    #         vel = self.settings[ax_name + "_velocity"]
    #
    #     scale = self.settings[ax_name + "_step_convert"]  # step/mm
    #     self.dev.write_velocity_params(ax_num, int(
    #         round(scale * acc)), int(round(scale * vel)))
    #     self.dev.write_homing_velocity(ax_num, int(round(scale * vel)))

    def New_quick_UI(self, include=('connected',
                                    'is_homed',
                                    'is_homing',
                                    'is_moving'
                                    )):
        from qtpy import QtWidgets
        S = self.settings
        widget = QtWidgets.QGroupBox(title=self.name)
        main_layout = QtWidgets.QVBoxLayout(widget)
        main_layout.addWidget(self.settings.New_UI(include))
        h_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(h_layout)
        # for axis in axes:
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(S.get_lq(f"position").new_default_widget())
        layout.addWidget(
            S.get_lq(f"target_position").new_default_widget())
        for sign in ('forward', 'backward'):
            layout.addWidget(self.new_operation_push_buttons(f'jog {sign}'))
        stop_btn = self.new_operation_push_buttons(f'stop')
        stop_btn.setStyleSheet('color:red; font-weight: bold;')
        layout.addWidget(stop_btn)
        layout.addWidget(self.new_operation_push_buttons('home'))
        h_layout.addLayout(layout)
        widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                             QtWidgets.QSizePolicy.Maximum)
        return widget

    def new_operation_push_buttons(self, name):
        from qtpy.QtWidgets import QPushButton
        btn = QPushButton(name)
        btn.clicked.connect(self.operations[name])
        return btn
