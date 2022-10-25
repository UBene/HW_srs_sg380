from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QCompleter, QLineEdit

from ScopeFoundry.measurement import Measurement

from .editors import EditorUI
from .item import Item


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


class UpdateSettingEditorUI(EditorUI):

    item_type = 'update-setting'
    description = "update a setting with value, a setting or __<iteration letter>"

    def __init__(self, measure: Measurement, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):
        self.setting_cb = QComboBox()
        self.setting_cb.setEditable(True)
        self.setting_cb.addItems(self.paths)
        self.setting_cb.setToolTip('setting to update')
        self.completer = completer = QCompleter(self.paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_cb.setCompleter(completer)
        self.group_box.layout().addWidget(self.setting_cb)
        self.value_le = QLineEdit()
        _paths = self.paths + ["True", "False", "__A", "__B", "__C", "__D"]
        completer = QCompleter(_paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.value_le.setCompleter(completer)
        self.value_le.setToolTip('''value used to update. Can be a value, a setting, 
                                            or '__<iteration letter>' ''')
        self.group_box.layout().addWidget(self.value_le)

    def get_kwargs(self):
        path = self.setting_cb.currentText()
        val = self.value_le.text()
        return {'setting': path, 'value': val}

    def edit_item(self, **kwargs):
        self.setting_cb.setCurrentText(kwargs['setting'])
        self.value_le.setText(kwargs['value'])
        self.value_le.selectAll()
        self.value_le.setFocus()
