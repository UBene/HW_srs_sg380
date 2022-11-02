'''
Created on Sep 17, 2021

@author: Benedikt Ursprung
'''
import glob
import json
import os
import time
from builtins import getattr

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout,
                            QPushButton, QVBoxLayout, QWidget)

from ScopeFoundry import Measurement

from .editors import Editor, EditorUI
from .item import Item
from .item_factory import item_factory
from .items import Items
from .types.dir_operations import NewDirEditorUI, SaveDirToParentEditorUI
from .types.exec_function import ExecFunction
from .types.interrupt_if import IterruptIfEditorUI
from .types.iterations import (InterationsEditor, IterationsEditorUI,
                               link_iteration_items)
from .types.pause import PauseEditorUI
from .types.read_from_hardware import ReadFromHardWareEditorUI
from .types.run_measurement import RunMeasurementEditorUI
from .types.timeout import TimeoutEditorUI
from .types.update_settings import UpdateSettingEditorUI
from .types.wait_until import WaitUntilEditorUI


class Sequencer(Measurement):

    name = 'sequencer'

    def setup(self):
        self.settings.New('cycles', int, initial=1,
                          description='number of times the sequence is executed')
        self.settings.New('paused', bool, initial=False)
        self.iter_values = {}
        self.letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def setup_figure(self):
        self.ui = QWidget()
        self.layout = QVBoxLayout(self.ui)

        # measurement controls and settings
        layout = QHBoxLayout()
        layout.addWidget(self.settings.cycles.new_default_widget())
        layout.addWidget(self.settings.activation.new_pushButton())
        btn = self.settings.paused.new_pushButton(texts=['pause', 'resume'],
                                                  colors=[None, 'rgba( 0, 255, 0, 220)'])
        layout.addWidget(btn)
        self.layout.addLayout(layout)

        # select file combobox
        self.load_file_comboBox = QComboBox()
        self.update_load_file_comboBox()
        self.load_file_comboBox.currentTextChanged.connect(
            self.on_load_file_comboBox_changed)
        self.layout.addWidget(self.load_file_comboBox)

        # item list
        self.items = Items()
        self.layout.addWidget(self.items.get_widget())
        self.items.connect_item_double_clicked(self.item_double_clicked)

        # controls
        layout = QHBoxLayout()
        self.layout.addLayout(layout)
        self.remove_pushButton = QPushButton('remove selected item')
        self.remove_pushButton.setToolTip('DEL')
        self.remove_pushButton.clicked.connect(self.on_remove_item)
        layout.addWidget(self.remove_pushButton)
        btn = QPushButton('save list ...')
        btn.clicked.connect(self.on_save)
        layout.addWidget(btn)
        btn = QPushButton('load list ...')
        btn.clicked.connect(self.on_load)
        layout.addWidget(btn)
        btn = QPushButton('run selected item')
        btn.setToolTip('SPACEBAR')
        btn.clicked.connect(self.on_run_item_and_proceed)
        layout.addWidget(btn)
        self.show_editor_checkBox = QCheckBox('show|hide editor')
        layout.addWidget(self.show_editor_checkBox)

        # Editors
        self.editors: dict[str, Editor] = {}
        self.editor_widget = QWidget()
        self.editor_layout = QVBoxLayout()
        self.editor_widget.setLayout(self.editor_layout)
        self.layout.addWidget(self.editor_widget)
        self.show_editor_checkBox.stateChanged.connect(
            self.editor_widget.setVisible)
        self.show_editor_checkBox.setChecked(True)

        paths = self.app.lq_paths_list()
        all_functions = self.get_all_functions()

        self.register_editor(ReadFromHardWareEditorUI(self, paths))
        self.register_editor(UpdateSettingEditorUI(self, paths))
        self.register_editor(RunMeasurementEditorUI(self))
        self.register_editor(WaitUntilEditorUI(self, paths))
        self.register_editor(WaitUntilEditorUI(self, paths))
        self.register_editor(ExecFunction(self, all_functions))
        self.register_editor(PauseEditorUI(self))
        self.register_editor(IterruptIfEditorUI(self, paths))
        self.register_editor(NewDirEditorUI(self))
        self.register_editor(SaveDirToParentEditorUI(self))
        self.register_editor(TimeoutEditorUI(self))
        self.register_interation_editor(IterationsEditorUI(self, paths))

        for editor in self.editors.values():
            self.editor_layout.addWidget(editor.ui.group_box)

        self.editor_widget.keyPressEvent = self._editorKeyPressEvent
        self.items.get_widget().keyReleaseEvent = self._keyReleaseEvent

    def register_editor(self, editor_ui: EditorUI):
        self.editors[editor_ui.item_type] = Editor(editor_ui)

    def register_interation_editor(self, editor_ui: IterationsEditorUI):
        editor = InterationsEditor(editor_ui)
        self.editors['start-iteration'] = editor
        self.editors['end-iteration'] = editor

    def _editorKeyPressEvent(self, event):
        if not event.modifiers() & Qt.ControlModifier:
            return
        if not event.key() in (Qt.Key_R, Qt.Key_N):
            return
        fw = self.editor_widget.focusWidget()
        # find editor with focused widget
        for e in self.editors.values():
            gb = e.ui.group_box
            if fw in gb.findChildren(type(fw), fw.objectName()):
                if event.key() == Qt.Key_R:
                    e.on_replace_func()
                if event.key() == Qt.Key_N:
                    e.on_new_func()

    def _keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.items.remove()
        if event.key() == Qt.Key_Space:
            self.on_run_item_and_proceed()
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            item = self.items.get_current_item()
            self.item_double_clicked(item)

    def update_load_file_comboBox(self):
        fnames = glob.glob(glob.os.getcwd() +
                           '\..\..\**/*.json', recursive=True)
        index0 = self.load_file_comboBox.currentIndex()
        self.load_file_comboBox.clear()
        self.seq_fnames = {}
        for fname in fnames:
            abbrev_fname = '\\'.join(fname.split('\\')[-2:])
            self.seq_fnames.update({abbrev_fname: fname})
        self.load_file_comboBox.addItems(list(self.seq_fnames.keys()))
        self.load_file_comboBox.setCurrentIndex(index0)

    def on_load_file_comboBox_changed(self, fname):
        self.load_file(self.seq_fnames[fname])

    def next_iter_id(self):
        return self.letters[self.items.count_type('start-iteration')]

    def on_remove_item(self):
        self.items.remove(None)

    def on_save(self):
        fname, _ = QFileDialog.getSaveFileName(
            self.ui, caption=u'Save Sequence', filter=u"Sequence (*.json)")
        if fname:
            self.save_to_file(fname)
        self.update_load_file_comboBox()
        return fname

    def save_to_file(self, fname):
        with open(fname, "w+") as f:
            f.write(json.dumps(self.items.as_dicts(), indent=1))

    def on_load(self):
        fname, _ = QFileDialog.getOpenFileName(
            None, filter=u"Sequence (*.json)")
        if fname:
            self.load_file(fname)
        return fname

    def load_file(self, fname):
        self.items.clear()
        with open(fname, "r") as f:
            lines = json.loads(f.read())
        for kwargs in lines:
            item_type = kwargs.pop('type')
            item = item_factory(self, item_type, **kwargs)
            self.items.add(item)
        success = link_iteration_items(self.items)
        if not success:
            print("invalid list")

    def on_run_item(self):
        item = self.items.get_current_item()
        if item.item_type == 'measurement':
            print('WARNING measurement not supported without running threat')
            return (item, None)
        else:
            return (item, self.items.get_current_item().visit())

    def on_run_item_and_proceed(self):
        item, next_item = self.on_run_item()
        if next_item == None:
            row = self.items.get_row(item)
            next_item = self.items.get_item(row + 1)
        self.items.set_current_item(next_item)

    def item_double_clicked(self, item: Item):
        # print('item_double_clicked', item.item_type, item.kwargs)
        self.editors[item.item_type].ui.edit_item(**item.kwargs)

    def run(self):
        success = link_iteration_items(self.items)
        if not success:
            print("invalid list")

        N = self.items.count()
        for i in range(N):
            self.items.get_item(i).reset()

        for q in range(self.settings['cycles']):
            # pct = int(100 * q / self.settings['cycles'])
            # self.set_progress(pct)
            if self.interrupt_measurement_called:
                break

            # go through list
            row = 0
            while row < self.items.count():

                while self.settings['paused']:
                    if self.interrupt_measurement_called:
                        break
                    time.sleep(0.03)

                # print('current j', j, N)
                self.current_item = item = self.items.get_item(row)

                resp = item.visit()
                if resp is None:
                    # go to next item
                    row += 1
                else:
                    # jump to item returned
                    row = self.items.get_row(resp)

                if self.interrupt_measurement_called:
                    break

        self.current_item = None

    def update_display(self):
        for i in range(self.items.count()):
            item = self.items.get_item(i)
            if item == self.current_item:
                item.setBackground(Qt.green)
            else:
                item.setBackground(Qt.white)

    def shutdown(self):
        os.system("shutdown /s /f /t 1")

    def restart(self):
        os.system("restart /r /f /t 1")

    def get_all_functions(self):
        funcs = []

        def append_objs_callables(obj, from_app_path):
            for a in dir(obj):
                try: # Not sure why some python version seem to need this block
                    if callable(getattr(obj, a)) and a.startswith('__') is False:
                        funcs.append(f'{from_app_path}{obj.name}.{a}')
                except AttributeError as e:
                    print(e)
        append_objs_callables(self.app, "")
        for m in self.app.measurements.values():
            append_objs_callables(m, 'measurements.')
        for h in self.app.hardware.values():
            append_objs_callables(h, 'hardware.')
        return funcs