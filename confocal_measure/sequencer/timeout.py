import time

from qtpy.QtWidgets import QDoubleSpinBox

from .editors import EditorUI
from .item import Item


class Timeout(Item):

    item_type = 'timeout'

    def visit(self):
        t0 = time.time()
        while True:
            dt = time.time() - t0
            if self.measure.interrupt_measurement_called or dt > self.kwargs['time']:
                break
            time.sleep(0.50)


class TimeoutEditorUI(EditorUI):

    item_type = 'timeout'
    description = 'wait for a bit'

    def setup_ui(self):
        time_out_layout = self.group_box.layout()
        self.time_dsb = QDoubleSpinBox()
        self.time_dsb.setValue(0.1)
        self.time_dsb.setToolTip('time-out in sec')
        self.time_dsb.setMaximum(1e6)
        self.time_dsb.setDecimals(3)
        time_out_layout.addWidget(self.time_dsb)

    def get_kwargs(self):
        return {'time': self.time_dsb.value()}

    def edit_item(self, **kwargs):
        self.time_dsb.setValue(kwargs['time'])
        self.time_dsb.selectAll()
        self.time_dsb.setFocus()
