import operator

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QCompleter, QLineEdit

from .editors import EditorUI
from .list_items import Item


class InterruptIf(Item):

    item_type = 'interrupt-if'

    def visit(self):
        relate = {'=': operator.eq, '>': operator.gt,
                  '<': operator.lt}[self.kwargs['operator']]
        lq = self.app.lq_path(self.kwargs['setting'])
        val = lq.coerce_to_type(self.kwargs['value'])
        if relate(lq.val, val):
            self.measure.interrupt()


class IterruptIfEditorUI(EditorUI):

    item_type = 'interrupt-if'
    description = 'interrupt if a condition is met'

    def __init__(self, measure, paths) -> None:
        self.paths = paths 
        super().__init__(measure)

    def setup_ui(self):
        paths = self.paths
        interrupt_if_layout = self.group_box.layout()
        self.setting_comboBox = QComboBox()
        self.setting_comboBox.setEditable(True)
        self.setting_comboBox.addItems(paths)
        self.setting_comboBox.setToolTip('setting')
        self.completer = completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_comboBox.setCompleter(completer)
        interrupt_if_layout.addWidget(self.setting_comboBox)
        self.operator_comboBox = QComboBox()
        self.operator_comboBox.addItems(['=', '<', '>'])
        interrupt_if_layout.addWidget(self.operator_comboBox)
        self.value_lineEdit = QLineEdit()
        interrupt_if_layout.addWidget(self.value_lineEdit)

    def get_kwargs(self):
        path = self.setting_comboBox.currentText()
        o = self.operator_comboBox.currentText()
        val = self.value_lineEdit.text()
        return {'setting': path, 'operator': o, 'value': val}

    def on_focus(self, d):
        self.setting_comboBox.setEditText(d['setting'])
        self.operator_comboBox.setEditText(d['operator'])
        self.value_lineEdit.setText(d['val'])
    