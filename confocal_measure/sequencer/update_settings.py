from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QCompleter, QLineEdit

from ScopeFoundry.measurement import Measurement

from .editors import EditorUI
from .list_items import Item


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

    type_name = 'update-setting'
    description = "update a setting with value, a setting, read_from_hardware or __<iteration letter>"

    def __init__(self, measure: Measurement, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):
        # # setting-update
        gb = self.group_box
        paths = self.paths
        self.setting_comboBox = QComboBox()
        self.setting_comboBox.setEditable(True)
        self.setting_comboBox.addItems(paths)
        self.setting_comboBox.setToolTip('setting to update')
        self.completer = completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_comboBox.setCompleter(completer)
        gb.layout().addWidget(self.setting_comboBox)
        self.setting_lineEdit = QLineEdit()
        _paths = paths + ["read_from_hardware", "True",
                          "False", "__A", "__B", "__C", "__D"]
        completer = QCompleter(_paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_lineEdit.setCompleter(completer)
        self.setting_lineEdit.setToolTip('''value used to update. Can be a value, a setting, 
                                            or '__<iteration letter>' ''')
        gb.layout().addWidget(self.setting_lineEdit)

    def get_kwargs(self):
        path = self.setting_comboBox.currentText()
        val = self.setting_lineEdit.text()
        return {'setting': path, 'value': val}


    def on_focus(self, d):
        self.setting_comboBox.setCurrentText(d['setting'])
        self.setting_lineEdit.setText(d['value'])
        self.setting_lineEdit.selectAll()
        self.setting_lineEdit.setFocus()