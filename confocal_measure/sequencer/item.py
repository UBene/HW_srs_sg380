
import operator
from datetime import datetime
from pathlib import Path
from time import time

from qtpy.QtWidgets import QListWidgetItem
from typing_extensions import Self

from ScopeFoundry.measurement import Measurement


class Item(QListWidgetItem):

    item_type = 'item - overwrite me'

    def __init__(self, measure: Measurement, **kwargs):
        super().__init__()
        self.app = measure.app
        self.measure = measure
        self.kwargs = kwargs
        self.update_appearance()

    def visit(self) -> None | Self:
        raise NotImplementedError

    def update_appearance(self, text=None):
        if text == None:
            x = [f'{val}' for key, val in self.kwargs.items()]
            text = f"{self.item_type}: {' '.join(x)}"
        self.setText(text)
        return text

    def reset(self):
        pass
