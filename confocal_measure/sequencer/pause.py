from ast import operator
from time import time

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDoubleSpinBox,
                            QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                            QLineEdit, QListWidget, QListWidgetItem,
                            QPushButton, QSpacerItem, QSpinBox, QVBoxLayout,
                            QWidget)

from .editors import Editor, EditorUI
from .item import Item


class Pause(Item):

    item_type = 'pause'

    def visit(self):
        self.measure.settings['paused'] = True


class PauseEditorUI(EditorUI):

    item_type = 'pause'
    description = 'pauses - click resume'

    def __init__(self, measure) -> None:
        super().__init__(measure)

    def setup_ui(self):

        self.pause_spacer = QLabel()
        self.group_box.layout().addWidget(self.pause_spacer)

    def get_kwargs(self):
        return {'info': "click resume to continue"}

    def edit_item(self, **kwargs):
        self.pause_spacer.setFocus()
