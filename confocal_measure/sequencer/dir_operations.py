from datetime import datetime
from pathlib import Path
from time import time

from qtpy.QtWidgets import QLabel, QLineEdit

from .editors import EditorUI
from .list_items import Item


class NewDir(Item):

    item_type = 'new_dir'

    def visit(self):
        t0 = time.time()
        name = self.kwargs['new_dir_name']
        sub_dir = f"{datetime.fromtimestamp(t0):%y%m%d_%H%M%S}_{name}"
        new_dir = Path(self.app.settings['save_dir']) / sub_dir
        new_dir.mkdir()
        self.app.settings['save_dir'] = new_dir.as_posix()

class NewDirEditorUI(EditorUI):

    item_type = 'new_dir'
    description = f'creates sub folder and set as save_dir'


    def setup_ui(self):

        self.new_dir_name_lineEdit = QLineEdit()
        self.group_box.layout().addWidget(self.new_dir_name_lineEdit)


    def get_kwargs(self):
        val = self.new_dir_name_lineEdit.text()
        return {'new_dir_name': val,
             'info': "creates new_dir_name sub-folder and sets save_dir"}

    def on_focus(self, d):
        self.new_dir_name_lineEdit.setText(d['new_dir_name'])


class SaveDirToParent(Item):

    item_type = 'save_dir_to_parent'

    def visit(self):
        cur = Path(self.app.settings['save_dir'])
        self.app.settings['save_dir'] = cur.parent.as_posix()



class SaveDirToParentEditorUI(EditorUI):

    item_type = 'save_dir_to_parent'
    description = 'save_dir to parent, designed use in conjunction with new_dir'

    def setup_ui(self):
        self.spacer = QLabel()
        self.group_box.layout().addWidget(self.spacer)
        
    def get_kwargs(self):
        return {'info': "click resume to continue"}

    def on_focus(self, d):
        self.spacer.setFocus()
