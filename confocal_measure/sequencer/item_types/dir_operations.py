import time
from datetime import datetime
from pathlib import Path
from typing_extensions import TypedDict

from qtpy.QtWidgets import QLabel, QLineEdit

from ..editors import EditorUI
from ..item import Item
from .item_factory import register_item


class NewDirKwargs(TypedDict):
    new_dir_name: str


class NewDir(Item):

    item_type = 'new_dir'

    def visit(self):
        t0 = time.time()
        name = self.kwargs['new_dir_name']
        sub_dir = f"{datetime.fromtimestamp(t0):%y%m%d_%H%M%S}_{name}"
        new_dir = Path(self.app.settings['save_dir']) / sub_dir
        new_dir.mkdir()
        self.app.settings['save_dir'] = new_dir.as_posix()


register_item(NewDir)


class NewDirEditorUI(EditorUI):

    item_type = 'new_dir'
    description = f'creates sub folder and set as save_dir'

    def setup_ui(self):

        self.new_dir_name_lineEdit = QLineEdit()
        self.group_box.layout().addWidget(self.new_dir_name_lineEdit)

    def get_kwargs(self):
        val = self.new_dir_name_lineEdit.text()
        return {'new_dir_name': val}

    def edit_item(self, **kwargs):
        self.new_dir_name_lineEdit.setText(kwargs['new_dir_name'])


class SaveDirToParent(Item):

    item_type = 'save_dir_to_parent'

    def visit(self):
        cur = Path(self.app.settings['save_dir'])
        self.app.settings['save_dir'] = cur.parent.as_posix()


register_item(SaveDirToParent)


class SaveDirToParentKwargs(TypedDict):
    info: str


class SaveDirToParentEditorUI(EditorUI):

    item_type = 'save_dir_to_parent'
    description = 'save_dir to parent, designed use in conjunction with new_dir'

    def setup_ui(self):
        self.spacer = QLabel()
        self.layout.addWidget(self.spacer)

    def get_kwargs(self) -> SaveDirToParentKwargs:
        return {'info': 'save_dir jumps to parent'}

    def edit_item(self, **kwargs):
        self.spacer.setFocus()
