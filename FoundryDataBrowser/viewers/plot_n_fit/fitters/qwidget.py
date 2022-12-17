"""
Created on Mar 9, 2022

@author: Benedikt Ursprung
"""
from qtpy import QtWidgets

from ScopeFoundry.logged_quantity import LoggedQuantity, LQCollection


class FitterQWidget(QtWidgets.QWidget):
    """ ui widget for  BaseFitter"""

    def __init__(self):
        super().__init__()
        self.layout = layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.result_label = QtWidgets.QLabel()
        layout.addWidget(QtWidgets.QLabel("<h3>results</h3>"))
        layout.addWidget(self.result_label)

    def add_collection_widget(self, collection: LQCollection, title):
        if len(collection):
            self.layout.addWidget(QtWidgets.QLabel(f"<h3>{title}</h3>"))
            widget = collection.New_UI()
            self.layout.addWidget(widget)
            return widget

    def add_enableable_collection_widget(
        self, collection: LQCollection, title: str, enable_setting: LoggedQuantity
    ):
        widget = self.add_collection_widget(collection, title)
        if widget:
            enable_setting.add_listener(lambda: widget.setEnabled(enable_setting.val))

    def add_button(self, name, callback_func):
        PB = QtWidgets.QPushButton(name)
        self.layout.addWidget(PB)
        PB.clicked.connect(callback_func)

    def set_result_message(self, text):
        self.result_label.setText(text)
