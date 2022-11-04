from typing_extensions import TypedDict

from qtpy.QtWidgets import QComboBox, QSpinBox

from .helper_func import new_q_completer
from .item_factory import register_item
from ..editors import EditorUI
from ..item import Item


class RunMeasurementKwargs(TypedDict):
    measurement: str
    repetitions: int


class RunMeasurement(Item):

    item_type = 'measurement'

    def visit(self):
        m = self.app.measurements[self.kwargs['measurement']]
        for i in range(self.kwargs['repetitions']):
            try:
                self.measure.start_nested_measure_and_wait(
                    m, nested_interrupt=False)
            except:
                print(self.measure, 'delegated', m.name, 'failed')


register_item(RunMeasurement)


class RunMeasurementEditorUI(EditorUI):

    item_type = 'measurement'
    description = "run a ScopeFoundry Measurement"

    def setup_ui(self):
        # # setting-update
        measure_layout = self.group_box.layout()
        measurements = self.measure.app.measurements.keys()
        self.measure_cb = QComboBox()
        self.measure_cb.setEditable(True)
        self.measure_cb.addItems(measurements)
        self.measure_cb.setCompleter(new_q_completer(measurements))
        measure_layout.addWidget(self.measure_cb)
        self.repetitions_sb = QSpinBox()
        self.repetitions_sb.setValue(1)
        self.repetitions_sb.setToolTip('number of repetitions')
        measure_layout.addWidget(self.repetitions_sb)

    def get_kwargs(self) -> RunMeasurementKwargs:
        k = self.measure_cb.currentText()
        reps = self.repetitions_sb.value()
        return {'measurement': k, 'repetitions': reps}

    def edit_item(self, **kwargs):
        self.measure_cb.setCurrentText(kwargs['measurement'])
        self.repetitions_sb.setValue(kwargs['repetitions'])
        self.measure_cb.setFocus()