from qtpy.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDoubleSpinBox,
                            QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                            QLineEdit, QListWidget, QListWidgetItem,
                            QPushButton, QSpacerItem, QSpinBox, QVBoxLayout,
                            QWidget)

from ScopeFoundry.measurement import Measurement

from .loader import new_item


class EditorUI:

    type_name = ""
    description = ""

    def __init__(self, measure: Measurement) -> None:
        self.measure = measure

        self.layout = layout = QHBoxLayout()
        self.group_box = gb = QGroupBox(self.type_name.replace('_', '-'))
        gb.setToolTip(self.description)
        gb.setLayout(layout)

        self.add_btn = add_btn = QPushButton('New')
        add_btn.setToolTip('CTRL+N')
        add_btn.setFixedWidth(30)
        layout.addWidget(add_btn)

        self.replace_btn = replace_btn = QPushButton('Replace')
        replace_btn.setFixedWidth(50)
        replace_btn.setToolTip('CTRL+R')
        layout.addWidget(replace_btn)
        self.setup_ui()

    def set_on_new_func(self, fn):
        self.add_btn.clicked.connect(fn)

    def set_on_replace_func(self, fn):
        self.replace_btn.clicked.connect(fn)

    def setup_ui(self):
        ...

    def get_kwargs(self):
        ...

    def on_focus(self):
        ...


class Editor:
    def __init__(self, editor_ui: EditorUI) -> None:
        self.ui = editor_ui
        self.type_name = editor_ui.type_name
        self.description = editor_ui.description
        self.ui = editor_ui
        self.ui.set_on_new_func(self.on_new_func)
        self.ui.set_on_replace_func(self.on_replace_func)

    def _new_item(self):
        print(self.ui.get_kwargs(), self.type_name)
        return new_item(self.ui.measure, self.type_name, **self.ui.get_kwargs())

    def on_new_func(self):
        self.ui.measure.item_list.add(self._new_item())

    def on_replace_func(self):
        self.ui.measure.replace(self._new_item())
