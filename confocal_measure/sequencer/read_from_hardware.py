from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDoubleSpinBox,
                            QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                            QLineEdit, QListWidget, QListWidgetItem,
                            QPushButton, QSpacerItem, QSpinBox, QVBoxLayout,
                            QWidget)

from .editors import Editor, EditorUI
from .item import Item


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
        self.layout.addWidget(self.setting_cb)

    def get_kwargs(self):
        return {'setting': self.setting_cb.currentText()}

    def edit_item(self, **kwargs):
        self.setting_cb.setCurrentText(kwargs['setting'])
        self.setting_cb.setFocus()
