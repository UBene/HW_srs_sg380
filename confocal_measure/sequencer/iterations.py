import numpy as np
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QComboBox, QCompleter, QDoubleSpinBox

from ScopeFoundry.measurement import Measurement

from .editors import Editor, EditorUI
from .list_items import Item


class StartIteration(Item):

    item_type = 'start-iteration'

    def __init__(self, measure, iter_id=None, text=None, **kwargs):
        self.iter_id = iter_id
        Item.__init__(self, measure=measure, text=text, **kwargs)
        self.reset()

    def update_d(self, d):
        Item.update_d(self, d)
        self.lq = self.app.lq_path(d['setting'])
        self.values = d['values']

    def update_appearance(self, text=None):
        text = Item.update_appearance(self, text=text)
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

    def __init__(self, measure, text=None, **kwargs):
        self.iter_id = None
        Item.__init__(self, measure=measure, text=text, **kwargs)
        self.break_next = False

    def update_appearance(self, text=None):
        text = Item.update_appearance(self, text=text)
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

    def set_start_iteration_item(self, start_iteration_item):
        self.start_iteration_item = start_iteration_item
        self.iter_id = start_iteration_item.iter_id
        self.update_appearance()

    def update_text(self):
        try:
            text = self.text().split(' - ')[0]
            pct = 100.0 * (self.start_iteration_item.idx + 1) / \
                (len(self.start_iteration_item.values))
            self.setText(text + f' - {pct: 1.0f} %')
        except:
            pass


class IterationsEditorUI(EditorUI):

    type_name = 'start-iteration'
    description = "a setting is iterated over a range of values"

    def __init__(self, measure: Measurement, paths) -> None:
        self.paths = paths
        super().__init__(measure)

    def setup_ui(self):

        # # iteration

        iteration_layout = self.group_box.layout()
        self.iteration_comboBox = QComboBox()
        self.iteration_comboBox.setEditable(True)
        self.iteration_comboBox.addItems(self.paths)
        self.iteration_comboBox.setToolTip('setting')
        self.completer = completer = QCompleter(self.paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.iteration_comboBox.setCompleter(completer)
        iteration_layout.addWidget(self.iteration_comboBox)
        self.iteration_start_doubleSpinBox = QDoubleSpinBox()
        self.iteration_start_doubleSpinBox.setToolTip('start value')
        iteration_layout.addWidget(self.iteration_start_doubleSpinBox)
        self.iteration_stop_doubleSpinBox = QDoubleSpinBox()
        self.iteration_stop_doubleSpinBox.setToolTip('stop value')
        self.iteration_stop_doubleSpinBox.setValue(10)
        iteration_layout.addWidget(self.iteration_stop_doubleSpinBox)
        self.iteration_step_doubleSpinBox = QDoubleSpinBox()
        self.iteration_step_doubleSpinBox.setToolTip('step value')
        self.iteration_step_doubleSpinBox.setValue(1)
        iteration_layout.addWidget(self.iteration_step_doubleSpinBox)
        for spinBox in [self.iteration_start_doubleSpinBox,
                        self.iteration_step_doubleSpinBox,
                        self.iteration_stop_doubleSpinBox]:
            spinBox.setMinimum(-1e6)
            spinBox.setMaximum(1e6)
            spinBox.setDecimals(6)

    def on_focus(self, d):
        self.iteration_start_doubleSpinBox.setValue(d['values'][0])
        step = d['values'][1] - d['values'][0]
        self.iteration_step_doubleSpinBox.setValue(step)
        self.iteration_stop_doubleSpinBox.setValue(d['values'][-1] + step)
        self.iteration_start_doubleSpinBox.selectAll()
        self.iteration_start_doubleSpinBox.setFocus()

    def get_kwargs(self):
        path = self.iteration_comboBox.currentText()
        start = self.iteration_start_doubleSpinBox.value()
        stop = self.iteration_stop_doubleSpinBox.value()
        step = self.iteration_step_doubleSpinBox.value()
        values = list(np.arange(start, stop, step))
        return {'setting': path, 'values': values}


class InterationsEditor(Editor):

    def on_new_func(self):
        iter_id = self.ui.measure.next_iter_id()
        self.ui.measure.item_list.add(StartIteration(self.ui.measure, iter_id=iter_id, **self.ui.get_kwargs()))
        self.ui.measure.item_list.add(EndIteration(
            self.ui.measure, **self.ui.get_kwargs()))
