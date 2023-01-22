'''
Created on Sep 23, 2014
reworked Feb 04, 2022

@author: Benedikt 
'''
from ScopeFoundry import HardwareComponent
from .ell6k_dual_position_slider_dev import ELL6KDualPositionSliderDev


class ELL6KDualPositionSliderHW(HardwareComponent):

    name = 'dual_position_slider'

    def __init__(self, app, debug=False, name=None, choices=(('open', 0),
                                                             ('closed', 1))):
        assert len(choices) == 2
        if len(choices[0]) == 1:
            self.choices = [(x, i) for i, x in enumerate(choices)]
        else:
            self.choices = choices
        HardwareComponent.__init__(self, app, debug, name)

    def setup(self):
        self.settings.New('position',
                          int,
                          choices=self.choices)
        self.settings.New('port',
                          str,
                          initial='COM11')
        self.add_operation('toggle', self.toggle)

    def connect(self):
        S = self.settings
        self.dev = ELL6KDualPositionSliderDev(port=S['port'],
                                              debug=S['debug_mode'])
        S.position.connect_to_hardware(self.dev.read_position,
                                       self.dev.write_position)
        self.read_from_hardware()

    def toggle(self):
        self.settings['position'] = self.dev.read_other_position()

    def disconnect(self):
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev

    def New_quick_UI(self, include=('connected', 'position'), operations=('toggle',)):
        from qtpy import QtWidgets
        widget = QtWidgets.QGroupBox(title=self.name)
        layout = QtWidgets.QVBoxLayout(widget)
        layout.addWidget(self.settings.New_UI(include))
        widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                             QtWidgets.QSizePolicy.Maximum)
        for op in operations:
            layout.addWidget(self.new_operation_push_buttons(op))
        return widget

    def new_operation_push_buttons(self, name):
        from qtpy.QtWidgets import QPushButton
        btn = QPushButton(name)
        btn.clicked.connect(self.operations[name])
        return btn
