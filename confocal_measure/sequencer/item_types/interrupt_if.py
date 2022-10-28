import operator
from typing import TypedDict


from qtpy.QtWidgets import QComboBox, QLineEdit

from .helper_func import new_q_completer

from ..editors import EditorUI
from ..item import Item
from .item_factory import register_item


class InterruptIfKwargs(TypedDict):
    setting: str
    operator: str
    value: str

class InterruptIf(Item):

    item_type = 'interrupt-if'

    def visit(self):
        relate = {'=': operator.eq, '>': operator.gt,
                  '<': operator.lt}[self.kwargs['operator']]
        lq = self.app.lq_path(self.kwargs['setting'])
        val = lq.coerce_to_type(self.kwargs['value'])
        if relate(lq.val, val):
            self.measure.interrupt()


register_item(InterruptIf)


class IterruptIfEditorUI(EditorUI):

    item_type = 'interrupt-if'
    description = 'interrupt if a condition is met'

    def __init__(self, measure, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):
        self.setting_cb = QComboBox()
        self.setting_cb.setEditable(True)
        self.setting_cb.addItems(self.paths)
        self.setting_cb.setToolTip('setting')
        completer = new_q_completer(self.paths)
        self.setting_cb.setCompleter(completer)
        self.layout.addWidget(self.setting_cb)
        self.operator_cb = QComboBox()
        self.operator_cb.addItems(['=', '<', '>'])
        self.layout.addWidget(self.operator_cb)
        self.value_le = QLineEdit()
        self.value_le.setCompleter(completer)
        self.layout.addWidget(self.value_le)

    def get_kwargs(self) -> InterruptIfKwargs:
        path = self.setting_cb.currentText()
        o = self.operator_cb.currentText()
        val = self.value_le.text()
        return {'setting': path, 'operator': o, 'value': val}

    def edit_item(self, **kwargs):
        self.setting_cb.setEditText(kwargs['setting'])
        self.operator_cb.setEditText(kwargs['operator'])
        self.value_le.setText(kwargs['value'])
