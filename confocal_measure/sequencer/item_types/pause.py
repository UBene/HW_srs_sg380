from .item_factory import register_item
from qtpy.QtWidgets import QLabel

from ..editors import EditorUI
from ..item import Item


class Pause(Item):

    item_type = 'pause'

    def visit(self):
        self.measure.settings['paused'] = True

register_item(Pause)

class PauseEditorUI(EditorUI):

    item_type = 'pause'
    description = 'pauses - click resume'

    def setup_ui(self):
        self.pause_spacer = QLabel()
        self.group_box.layout().addWidget(self.pause_spacer)

    def get_kwargs(self) -> dict[str, str]:
        return {'info': "click resume to continue"}

    def edit_item(self, **kwargs):
        self.pause_spacer.setFocus()


