from typing import Any

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListWidget

from ScopeFoundry.measurement import Measurement

from .item import Item


class Items:

    def __init__(self):
        self.widget = QListWidget()
        self.widget.setDefaultDropAction(Qt.MoveAction)
        self.widget.setDragDropMode(QListWidget.DragDrop)

    def add(self, item: Item, row=None):
        if row == None:
            row = self.get_current_row()
        self.widget.insertItem(row + 1, item)
        self.widget.setCurrentRow(row + 1)

    def remove(self, item=None):
        if item is not None:
            row = self.get_row(item)
        else:
            row = self.get_current_row()
        item = self.widget.takeItem(row)
        # if hasattr(item, 'start_iteration_item'):
        #     item2 = self.widget.takeItem(
        #         self.widget.row(item.start_iteration_item))
        #     del item2
        # if hasattr(item, 'end_iteration_item'):
        #     item2 = self.widget.takeItem(
        #         self.widget.row(item.end_iteration_item))
        #     del item2
        del item

    def replace(self, new_item: Item, old_item:Item | None = None):
        if old_item is None:
            old_item = self.get_current_item()
        self.add(new_item, self.get_row(old_item))
        self.remove(old_item)

    def connect_item_double_clicked(self, fn):
        self.widget.itemDoubleClicked.connect(fn)

    def get_widget(self) -> QListWidget:
        return self.widget

    def get_row(self, item: Item) -> int:
        return self.widget.row(item)

    def get_item(self, row: int) -> Item:
        return self.widget.item(row)  # type: ignore

    def get_current_row(self) -> int:
        return self.widget.currentRow()

    def get_current_item(self) -> Item:
        return self.widget.currentItem()  # type: ignore

    def set_current_item(self, item: Item):
        self.widget.setCurrentItem(item)

    def clear(self):
        self.widget.clear()

    def count_type(self, item_type='start-iteration'):
        counter = 0
        for i in range(self.widget.count()):
            item = self.get_item(i)
            if item.item_type == item_type:
                counter += 1
        return counter

    def count(self) -> int:
        return self.widget.count()

    def as_dicts(self) -> list[dict[str, Any]]:
        l = []
        for i in range(self.widget.count()):
            item = self.get_item(i)
            l.append({'type': item.item_type, **item.kwargs})
        return l


class SMeasure(Measurement):
    iter_values: dict[str, str]
    items: Items
