import operator
from time import time

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QCompleter, QLineEdit

from ..editors import EditorUI
from ..item import Item


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
        self.setting_cb = QComboBox()
        self.setting_cb.setEditable(True)
        self.setting_cb.addItems(self.paths)
        self.setting_cb.setToolTip('setting')
        self.completer = completer = QCompleter(self.paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_cb.setCompleter(completer)
        self.layout.addWidget(self.setting_cb)
        self.operator_cb = QComboBox()
        self.operator_cb.addItems(['=', '<', '>'])
        self.layout.addWidget(self.operator_cb)
        self.value_le = QLineEdit()
        self.value_le.setToolTip(
            'wait until setting reaches this value')
        self.layout.addWidget(self.value_le)

    def get_kwargs(self):
        path = self.setting_cb.currentText()
        o = self.operator_cb.currentText()
        v = self.value_le.text()
        return {'setting': path, 'operator': o, 'value': v}

    def edit_item(self, **kwargs):
        self.setting_cb.setCurrentText(kwargs['setting'])
        self.operator_cb.setCurrentText(kwargs['operator'])
        self.value_le.setText(kwargs['value'])
        self.value_le.selectAll()
        self.value_le.setFocus()
