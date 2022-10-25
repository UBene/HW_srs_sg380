
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDoubleSpinBox,
                            QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                            QLineEdit, QListWidget, QListWidgetItem,
                            QPushButton, QSpacerItem, QSpinBox, QVBoxLayout,
                            QWidget)

from .editors import EditorUI
from .list_items import Item


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

class RunMeasurementEditorUI(EditorUI):

    type_name = 'measurement'
    description = "run a scopeFoundry Measurement"

    def setup_ui(self):
        # # setting-update
        measure_layout = self.group_box.layout()
        measurements = self.measure.app.measurements.keys()
        self.measure_comboBox = QComboBox()
        self.measure_comboBox.setEditable(True)
        self.measure_comboBox.addItems(measurements)
        self.completer = completer = QCompleter(measurements)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.measure_comboBox.setCompleter(completer)
        measure_layout.addWidget(self.measure_comboBox)
        self.measure_spinBox = QSpinBox()
        self.measure_spinBox.setValue(1)
        self.measure_spinBox.setToolTip('number of repeats')
        measure_layout.addWidget(self.measure_spinBox)

    def get_kwargs(self):
        k = self.measure_comboBox.currentText()
        reps = self.measure_spinBox.value()
        return {'measurement': k, 'repetitions': reps}

    def on_focus(self, d):
        self.measure_comboBox.setCurrentText(d['measurement'])
        self.measure_spinBox.setValue(d['repetitions'])
        self.measure_comboBox.setFocus()