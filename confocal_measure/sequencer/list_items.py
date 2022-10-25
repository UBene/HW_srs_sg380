
import operator
from datetime import datetime
from pathlib import Path
from time import time

from qtpy.QtWidgets import QListWidgetItem

from ScopeFoundry.measurement import Measurement


class Item(QListWidgetItem):

    def __init__(self, measure: Measurement, **kwargs):
        super().__init__()
        self.app = measure.app
        self.measure = measure
        self.kwargs = kwargs

    def visit(self):
        raise NotImplementedError

    def update_d(self, d):
        self.kwargs.update(d)
        self.update_appearance()

    def update_appearance(self, text=None):
        if text == None:
            x = [f'{val}' for key, val in self.kwargs.items() if key != 'type']
            text = f"{self.kwargs['type']}: {' '.join(x)}"
        self.setText(text)
        return text

    def reset(self):
        pass


