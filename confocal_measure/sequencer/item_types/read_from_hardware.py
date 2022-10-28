from typing import TypedDict


from qtpy.QtWidgets import QComboBox

from .helper_func import new_q_completer
from .item_factory import register_item

from ..editors import EditorUI
from ..item import Item


class ReadFromHardWareKwargs(TypedDict):
    setting: str


class ReadFromHardWare(Item):

    item_type = 'read_from_hardware'

    def visit(self):
        self.app.lq_path(self.kwargs['setting']).read_from_hardware()


register_item(ReadFromHardWare)


class ReadFromHardWareEditorUI(EditorUI):

    description = 'trigger read_from_hardware'
    item_type = 'read_from_hardware'

    def __init__(self, measure, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):
        self.setting_cb = QComboBox()
        self.setting_cb.setEditable(True)
        self.setting_cb.addItems(self.paths)
        self.setting_cb.setToolTip('setting to update')
        self.setting_cb.setCompleter(new_q_completer(self.paths))
        self.layout.addWidget(self.setting_cb)

    def get_kwargs(self) -> ReadFromHardWareKwargs:
        return {'setting': self.setting_cb.currentText()}

    def edit_item(self, **kwargs):
        self.setting_cb.setCurrentText(kwargs['setting'])
        self.setting_cb.setFocus()
