"""
Benedikt Ursprung
"""
from ScopeFoundry import HardwareComponent


class ThorlabsMFFHW(HardwareComponent):

    name = 'thorlabs_flipper'

    def __init__(self, app, debug=False, name=None, position_choices=('spectrometer', 'apd')):
        assert len(position_choices) == 2
        self.position_map = {position_choice: i + 1 for i,
                             position_choice in enumerate(position_choices)}
        super().__init__(app, debug, name)

    def setup(self):
        self.settings.New('serial_num',
                          dtype=str,
                          initial='37006062')
        self.settings.New("target_position", dtype=str,
                          choices=self.position_map)
        self.position_map["undefined"] = 0
        self.settings.New('position',
                          initial="undefined",
                          dtype=str,
                          choices=self.position_map,
                          ro=True)
        self.add_operation('Toggle', self.toggle_position)
        self.position_map_inv = {v: k for k, v in self.position_map.items()}

    def connect(self):
        if self.debug_mode.val:
            self.log.debug("Connecting to thorlabsMFF(debug)")

        if self.settings['serial_num'] == '37006062':
            # Suspect to have polling issue as device also does not work with
            # kinesis
            from .thorlabsMFF_polling_issue_device import ThorlabsMFFDev
        else:
            from .thorlabsMFF_device import ThorlabsMFFDev

        self.dev = ThorlabsMFFDev(
            self.settings['serial_num'],
            debug=self.settings['debug_mode']
        )

        self.settings.position.connect_to_hardware(
            read_func=self.read_position,
        )

        self.settings.target_position.connect_to_hardware(
            write_func=self.write_position
        )
        self.settings['serial_num'] = self.dev.serial_num_in_use
        self.read_from_hardware()

    def read_position(self):
        pos = self.dev.read_position()
        if self.settings['debug_mode']:
            print("read_position", pos)
        return self.position_map_inv.get(pos, 'undefined')

    def write_position(self, position):
        value = self.position_map[position]
        if self.settings['debug_mode']:
            print("write_position", position, value)
        self.dev.write_position(value)
        self.settings.position.read_from_hardware()

    def disconnect(self):
        # clean up hardware object
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

    def toggle_position(self):
        new_position = self.position_map_inv[self.dev.get_other_position()]
        self.settings['target_position'] = new_position

    def New_quick_UI(self):
        from qtpy import QtWidgets
        S = self.settings
        widget = QtWidgets.QGroupBox(title=self.name)
        main_layout = QtWidgets.QVBoxLayout(widget)
        main_layout.addWidget(self.settings.New_UI(('connected', 'position')))
        main_layout.addWidget(self.new_operation_push_buttons('Toggle'))
        widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                             QtWidgets.QSizePolicy.Maximum)
        return widget

    def new_operation_push_buttons(self, name):
        from qtpy.QtWidgets import QPushButton
        btn = QPushButton(name)
        btn.clicked.connect(self.operations[name])
        return btn
