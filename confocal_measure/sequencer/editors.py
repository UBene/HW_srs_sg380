from qtpy.QtWidgets import QGroupBox, QHBoxLayout, QPushButton

from .items import SMeasure
from .item_factory import item_factory


class EditorUI:

    item_type = ""
    description = ""

    def __init__(self, measure:SMeasure) -> None:
        self.measure = measure

        self.layout = layout = QHBoxLayout()
        self.group_box = gb = QGroupBox(self.item_type.replace('_', '-'))
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

    def edit_item(self, **kwargs):
        ...


class Editor:
    def __init__(self, editor_ui: EditorUI) -> None:
        self.ui = editor_ui
        self.item_type = editor_ui.item_type
        self.description = editor_ui.description
        self.ui = editor_ui
        self.ui.set_on_new_func(self.on_new_func)
        self.ui.set_on_replace_func(self.on_replace_func)

    def _new_item(self):
        return item_factory(self.ui.measure, self.item_type, **self.ui.get_kwargs())

    def on_new_func(self):
        self.ui.measure.items.add(self._new_item())

    def on_replace_func(self):
        self.ui.measure.items.replace(self._new_item())
