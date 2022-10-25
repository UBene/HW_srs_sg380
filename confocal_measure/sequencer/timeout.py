from ast import operator
from time import time

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDoubleSpinBox,
                            QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                            QLineEdit, QListWidget, QListWidgetItem,
                            QPushButton, QSpacerItem, QSpinBox, QVBoxLayout,
                            QWidget)

from .editors import Editor, EditorUI
from .list_items import Item


class Timeout(Item):

    item_type = 'timeout'

    def visit(self):
        t0 = time.time()
        while True:
            dt = time.time() - t0
            if self.measure.interrupt_measurement_called or dt > self.kwargs['time']:
                break
            time.sleep(0.05)



class TimeoutEditorUI(EditorUI):

    item_type = 'timeout'
    description = 'wait for a bit'

    def __init__(self, measure, paths) -> None:
         super().__init__(measure)
         self.paths = paths

    def setup_ui(self):
        paths = self.paths
        time_out_layout = self.group_box.layout()
        self.time_out_doubleSpinBox = QDoubleSpinBox()
        self.time_out_doubleSpinBox.setValue(0.1)
        self.time_out_doubleSpinBox.setToolTip('time-out in sec')
        self.time_out_doubleSpinBox.setMaximum(1e6)
        self.time_out_doubleSpinBox.setDecimals(3)
        time_out_layout.addWidget(self.time_out_doubleSpinBox)

    def get_kwargs(self):
        t = self.time_out_doubleSpinBox.value()
        return {'time': self.time_out_doubleSpinBox.value()}

    def on_focus(self, d):
        self.time_out_doubleSpinBox.setValue(d['time'])
        self.time_out_doubleSpinBox.selectAll()
        self.time_out_doubleSpinBox.setFocus()


