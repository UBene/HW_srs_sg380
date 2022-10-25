from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDoubleSpinBox,
                            QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                            QLineEdit, QListWidget, QListWidgetItem,
                            QPushButton, QSpacerItem, QSpinBox, QVBoxLayout,
                            QWidget)

from .editors import Editor, EditorUI
from .list_items import Item


class ReadFromHardWare(Item):

    item_type = 'read_from_hardware'

    def visit(self):
        self.app.lq_path(self.kwargs['setting']).read_from_hardware()


class ReadFromHardWareEditorUI(EditorUI):

    description = 'trigger read_from_hardware'
    item_type = 'read_from_hardware'

    def __init__(self, measure, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):
        # # setting-update
        gb = self.group_box
        self.setting_comboBox = QComboBox()
        self.setting_comboBox.setEditable(True)
        self.setting_comboBox.addItems(self.paths)
        self.setting_comboBox.setToolTip('setting to update')
        self.completer = completer = QCompleter(self.paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_comboBox.setCompleter(completer)
        gb.layout().addWidget(self.setting_comboBox)

    def get_kwargs(self):
        path = self.setting_comboBox.currentText()
        return {'setting': path}

    def on_focus(self, d):
        self.setting_comboBox.setCurrentText(d['setting'])
        self.setting_comboBox.setFocus()
