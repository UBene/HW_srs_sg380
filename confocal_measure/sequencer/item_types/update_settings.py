from .item_factory import register_item
from typing_extensions import TypedDict

from qtpy.QtWidgets import QComboBox, QLineEdit

from .helper_func import new_q_completer

from ..editors import EditorUI
from ..item import Item
from ..items import SMeasure


class UpdateSettingKwargs(TypedDict):
    setting: str
    value: str


class UpdateSetting(Item):

    item_type = 'update-setting'

    def visit(self):
        v = self.kwargs['value']
        try:
            v = self.app.lq_path(v).val
        except:
            pass
        if isinstance(v, str):
            if '__' in v:
                letter = v[v.find('__') + 2]
                v = self.measure.iter_values[letter]
        self.app.lq_path(self.kwargs['setting']).update_value(v)

register_item(UpdateSetting)

class UpdateSettingEditorUI(EditorUI):

    item_type = 'update-setting'
    description = "update a setting with value, a setting or __<iteration letter>"

    def __init__(self, measure: SMeasure, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):
        self.setting_cb = QComboBox()
        self.setting_cb.setEditable(True)
        self.setting_cb.addItems(self.paths)
        self.setting_cb.setToolTip('setting to update')
        self.completer = completer = new_q_completer(self.paths)
        self.setting_cb.setCompleter(completer)
        self.group_box.layout().addWidget(self.setting_cb)
        self.value_le = QLineEdit()
        completer = new_q_completer(
            self.paths + ["True", "False", "__A", "__B", "__C", "__D"])
        self.value_le.setCompleter(completer)
        self.value_le.setToolTip('''value used to update. Can be a value, a setting, 
                                            or '__<iteration letter>' ''')
        self.group_box.layout().addWidget(self.value_le)

    def get_kwargs(self) -> UpdateSettingKwargs:
        path = self.setting_cb.currentText()
        val = self.value_le.text()
        return {'setting': path, 'value': val}

    def edit_item(self, **kwargs):
        self.setting_cb.setCurrentText(kwargs['setting'])
        self.value_le.setText(kwargs['value'])
        self.value_le.selectAll()
        self.value_le.setFocus()


