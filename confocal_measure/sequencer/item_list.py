from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDoubleSpinBox,
                            QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                            QLineEdit, QListWidget, QListWidgetItem,
                            QPushButton, QSpacerItem, QSpinBox, QVBoxLayout,
                            QWidget)

from confocal_measure.sequencer.list_items import Item


class ItemList:

    def __init__(self):

        # list widget
        self.listWidget = QListWidget()
        self.listWidget.setDefaultDropAction(Qt.MoveAction)
        self.listWidget.setDragDropMode(QListWidget.DragDrop)

    def add(self, item: Item, row=None):
        if row == None:
            row = self.listWidget.currentIndex().row()
        self.listWidget.insertItem(row + 1, item)
        self.listWidget.setCurrentRow(row + 1)

    def remove(self, item=None):
        if item == None:
            item = self.listWidget.item(self.listWidget.currentRow())
        self.listWidget.takeItem(self.listWidget.row(item))
        if hasattr(item, 'start_iteration_item'):
            item2 = self.listWidget.takeItem(
                self.listWidget.row(item.start_iteration_item))
            del item2
        if hasattr(item, 'end_iteration_item'):
            item2 = self.listWidget.takeItem(
                self.listWidget.row(item.end_iteration_item))
            del item2

    def replace(self, new_item: Item):
        cur = self.get_current_item()
        if cur.type == new_item.type:
            cur.update_d(new_item.d)
            cur.update_appearance()

    def get_current_item(self) -> Item:
        return self.listWidget.currentItem()

    # def get_current_item_type(self):
    #     self.listWidget.currentItem().d['type']
