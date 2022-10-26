from typing import TypedDict

import numpy as np
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QCompleter, QDoubleSpinBox

from confocal_measure.sequencer.items import Items

from ..editors import Editor, EditorUI
from ..item import Item
from ..items import SMeasure


class StartIterationDict(TypedDict):
    values: list
    setting: str


class StartIteration(Item):

    item_type = 'start-iteration'

    def __init__(self, measure: SMeasure, **kwargs):
        self.iter_id = kwargs['iter_id']
        self.values = kwargs['values']
        self.lq = measure.app.lq_path(kwargs['setting'])
        Item.__init__(self, measure=measure, **kwargs)
        self.reset()

    def _update_appearance(self, text=None):
        text = Item._update_appearance(self, text=text)
        self.setText(f'__{self.iter_id} ' + text)

    def visit(self):
        self.idx += 1
        if self.idx == len(self.values) - 1:
            # next time end-iteration is visited the loop breaks
            self.end_iteration_item.break_next = True
        self.lq.update_value(self.values[self.idx])
        self.update_text()
        self.measure.iter_values.update({self.iter_id: self.values[self.idx]})
        self.val = self.values[self.idx]

    def reset(self):
        self.idx = -1
        self.update_text()

    def set_end_iteration_item(self, end_iteration_item):
        self.end_iteration_item = end_iteration_item

    def update_text(self):
        text = self.text().split(' - ')[0]
        pct = 100.0 * (self.idx + 1) / (len(self.values))
        if self.idx >= 0:
            texts = [text, f"({self.values[self.idx]})", f'{pct: 1.0f}%']
        else:
            texts = [text, f'{pct: 1.0f}%']
        self.setText(" - ".join(texts))


class EndIteration(Item):

    item_type = 'end-iteration'

    def __init__(self, measure: SMeasure, **kwargs):
        self.kwargs = kwargs
        self.iter_id = kwargs['iter_id']
        self.values = kwargs['values']
        self.lq = measure.app.lq_path(kwargs['setting'])
        Item.__init__(self, measure=measure, **kwargs)
        self.reset()

    def _update_appearance(self, text=None):
        text = Item._update_appearance(self, text=text)
        self.setText(f'__{self.iter_id} ' + text)

    def visit(self):
        self.update_text()
        if self.break_next:
            self.start_iteration_item.reset()
            self.reset()
            return None
        else:
            return self.start_iteration_item

    def reset(self):
        self.break_next = False
        self.update_text()

    def set_start_iteration_item(self, start_iteration_item: StartIteration):
        self.start_iteration_item = start_iteration_item
        self.iter_id = start_iteration_item.iter_id
        self._update_appearance()

    def update_text(self):
        try:
            text = self.text().split(' - ')[0]
            pct = 100.0 * (self.start_iteration_item.idx + 1) / \
                (len(self.start_iteration_item.values))
            self.setText(text + f' - {pct: 1.0f} %')
        except:
            pass


class IterationsEditorUI(EditorUI):

    item_type = 'start-iteration'
    description = "a setting is iterated over a range of values"

    def __init__(self, measure: SMeasure, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):
        self.setting_cb = QComboBox()
        self.setting_cb.setEditable(True)
        self.setting_cb.addItems(self.paths)
        self.setting_cb.setToolTip('setting')
        self.completer = completer = QCompleter(self.paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_cb.setCompleter(completer)
        self.layout.addWidget(self.setting_cb)
        self.start_dsb = QDoubleSpinBox()
        self.start_dsb.setToolTip('start value')
        self.layout.addWidget(self.start_dsb)
        self.stop_dsb = QDoubleSpinBox()
        self.stop_dsb.setToolTip('stop value')
        self.stop_dsb.setValue(10)
        self.layout.addWidget(self.stop_dsb)
        self.step_dsb = QDoubleSpinBox()
        self.step_dsb.setToolTip('step value')
        self.step_dsb.setValue(1)
        self.layout.addWidget(self.step_dsb)
        for spinBox in [self.start_dsb,
                        self.step_dsb,
                        self.stop_dsb]:
            spinBox.setMinimum(-1e6)
            spinBox.setMaximum(1e6)
            spinBox.setDecimals(6)

    def get_kwargs(self) -> StartIterationDict:
        path = self.setting_cb.currentText()
        start = self.start_dsb.value()
        stop = self.stop_dsb.value()
        step = self.step_dsb.value()
        values = list(np.arange(start, stop, step))
        return {'setting': path, 'values': values}

    def edit_item(self, **kwargs):
        self.start_dsb.setValue(kwargs['values'][0])
        step = kwargs['values'][1] - kwargs['values'][0]
        self.step_dsb.setValue(step)
        self.stop_dsb.setValue(kwargs['values'][-1] + step)
        self.start_dsb.selectAll()
        self.start_dsb.setFocus()


class InterationsEditor(Editor):

    def __init__(self, editor_ui: IterationsEditorUI) -> None:
        super().__init__(editor_ui)
        self.ui = editor_ui

    def on_new_func(self):
        iter_id = self.ui.measure.next_iter_id()
        self.ui.measure.items.add(StartIteration(
            self.ui.measure, iter_id=iter_id, **self.ui.get_kwargs()))
        self.ui.measure.items.add(EndIteration(
            self.ui.measure, iter_id=iter_id, **self.ui.get_kwargs()))
        link_iteration_items(self.ui.measure.items)

    def on_replace_func(self):
        items = self.ui.measure.items
        cur_item = items.get_current_item()

        if isinstance(cur_item, StartIteration):
            start_item = cur_item
            end_item = cur_item.end_iteration_item
            iter_id = cur_item.iter_id
        elif isinstance(cur_item, EndIteration):
            start_item = cur_item.start_iteration_item
            end_item = cur_item
            iter_id = cur_item.iter_id
        else:
            return

        items.replace(StartIteration(
            self.ui.measure, iter_id=iter_id, **self.ui.get_kwargs()), start_item)
        items.replace(EndIteration(
            self.ui.measure, iter_id=iter_id, **self.ui.get_kwargs()), end_item)
        link_iteration_items(items)


def link_iteration_items(item_list: Items) -> bool:
    '''returns if the list is valid in terms iteration items'''
    start_iter_items: list[StartIteration] = []
    for i in range(item_list.count()):
        item = item_list.get_item(i)
        if isinstance(item, StartIteration):
            start_iter_items.append(item)
        if isinstance(item, EndIteration):
            s_item = start_iter_items.pop()
            item.set_start_iteration_item(s_item)
            s_item.set_end_iteration_item(item)

    if len(start_iter_items) != 0:
        return False
    return True
