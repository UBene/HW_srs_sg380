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


class WaitUntil(Item):

    item_type = 'wait-until'

    def visit(self):

        relate = {'=': operator.eq, '>': operator.gt,
                  '<': operator.lt}[self.kwargs['operator']]
        lq = self.app.lq_path(self.kwargs['setting'])
        val = lq.coerce_to_type(self.kwargs['value'])
        while True:
            if relate(lq.val, val) or self.measure.interrupt_measurement_called:
                break
            time.sleep(0.05)


class WaitUntilEditorUI(EditorUI):

    item_type = 'wait-until'
    description = 'wait until condition is met'

    def __init__(self, measure, paths) -> None:
         self.paths = paths
         super().__init__(measure)

    def setup_ui(self):
        paths = self.paths
        wait_until_layout = self.group_box.layout()
        self.wait_until_comboBox = QComboBox()
        self.wait_until_comboBox.setEditable(True)
        self.wait_until_comboBox.addItems(paths)
        self.wait_until_comboBox.setToolTip('setting')
        self.completer = completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.wait_until_comboBox.setCompleter(completer)
        wait_until_layout.addWidget(self.wait_until_comboBox)
        self.wait_until_operator_comboBox = QComboBox()
        self.wait_until_operator_comboBox.addItems(['=', '<', '>'])
        wait_until_layout.addWidget(self.wait_until_operator_comboBox)
        self.wait_until_lineEdit = QLineEdit()
        self.wait_until_lineEdit.setToolTip(
            'wait until setting reaches this value')
        wait_until_layout.addWidget(self.wait_until_lineEdit)

    def get_kwargs(self):
        path = self.setting_comboBox.currentText()
        return {'setting': path}

    def on_focus(self, d):

            self.wait_until_comboBox.setCurrentText(d['setting'])
            self.wait_until_operator_comboBox.setCurrentText(d['operator'])
            self.wait_until_lineEdit.setText(d['value'])
            self.wait_until_lineEdit.selectAll()
            self.wait_until_lineEdit.setFocus()