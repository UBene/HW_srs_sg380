'''
Created on Sep 17, 2021

@author: Benedikt Ursprung
'''
import glob
import json
import os
import time
from builtins import getattr

from qtpy.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout,
                            QPushButton, QVBoxLayout, QWidget)

from ScopeFoundry import Measurement

from .dir_operations import NewDirEditorUI, SaveDirToParentEditorUI
from .editors import Editor, EditorUI
from .exec_function import ExecFunction
from .interrupt_if import IterruptIfEditorUI
from .item_list import ItemList
from .iterations import InterationsEditor, IterationsEditorUI
from .list_items import Item
from .pause import PauseEditorUI
from .read_from_hardware import ReadFromHardWareEditorUI
from .run_measurement import RunMeasurementEditorUI
from .update_settings import UpdateSettingEditorUI
from .wait_until import WaitUntilEditorUI


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

        # list widget
        # self.listWidget = QListWidget()
        # self.listWidget.setDefaultDropAction(Qt.MoveAction)
        # self.listWidget.setDragDropMode(QListWidget.DragDrop)

        self.item_list = ItemList()
        self.layout.addWidget(self.item_list.listWidget)
        self.item_list.listWidget.itemDoubleClicked.connect(
            self.on_itemDoubleClicked)
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

        self.listWidget = self.item_list.listWidget

        # Editors
        self.editors = {}
        self.editor_widget = QWidget()
        self.editor_layout = QVBoxLayout()
        self.editor_widget.setLayout(self.editor_layout)
        self.layout.addWidget(self.editor_widget)
        self.show_editor_checkBox.stateChanged.connect(
            self.editor_widget.setVisible)
        self.show_editor_checkBox.setChecked(True)

        paths = self.app.lq_paths_list()
        all_functions = self.all_functions()

        self._add_editor(ReadFromHardWareEditorUI(self, paths))
        self._add_editor(UpdateSettingEditorUI(self, paths))
        self._add_editor(RunMeasurementEditorUI(self))
        self._add_editor(WaitUntilEditorUI(self, paths))
        self._add_editor(WaitUntilEditorUI(self, paths))
        self._add_editor(ExecFunction(self, all_functions))
        self._add_editor(PauseEditorUI(self))
        self._add_editor(IterruptIfEditorUI(self, paths))
        self._add_editor(NewDirEditorUI(self))
        self._add_editor(SaveDirToParentEditorUI(self))
        self.editors['iterations']=InterationsEditor(IterationsEditorUI(self, paths))

        for editor in self.editors.values():
            self.editor_layout.addWidget(editor.ui.group_box)

    def _add_editor(self, editor_ui: EditorUI):
        self.editors[editor_ui.type_name] = Editor(editor_ui)




    # def _keyReleaseEvent(self, event):
    #     if event.key() == Qt.Key_Delete:
    #         self.on_remove_item()
    #     if event.key() == Qt.Key_Space:
    #         self.on_run_item_and_proceed()
    #     if event.key() in (Qt.Key_Enter, Qt.Key_Return):
    #         print(event.key())
    #         item = self.listWidget.currentItem()
    #         self.on_itemDoubleClicked(item)

    # def _editorKeyPressEvent(self, event):
    #     # find editor with focused widget
    #     if event.modifiers() & Qt.ControlModifier and event.key() in (Qt.Key_R, Qt.Key_N):
    #         fw = self.editors.widget.focusWidget()
    #         for key, val in self.editors.editors.items():
    #             for item in val['groubBox'].children():
    #                 if fw == item:
    #                     type_name = key
    #                     if event.key() == Qt.Key_R:
    #                         self.editors.editors[type_name]['on_replace_func'](
    #                         )
    #                     if event.key() == Qt.Key_N:
    #                         self.editors.editors[type_name]['on_add_func']()
    #     else:
    #         if event.key() in (Qt.Key_F1,):
    #             self.listWidget.setFocus()

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

    def add_listItem(self, d, text=None, row=None):
        item = self.new_item(d, text)
        self.item_list.add(item, row)

    def next_iter_id(self):
        return self.letters[self.iterations_count]

    def new_item(self, d, text):
        if d['type'] == 'start-iteration':
            iter_id = self.letters[self.iterations_count]
            item = StartIteration(
                self.app, self, d, iter_id, text)
        elif d['type'] == 'end-iteration':
            item = EndIteration(self.app, self, d, text)
        else:
            item = Item(self.app, self, d, text)
        return item

    @property
    def iterations_count(self):
        counter = 0
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.type_name == 'start-iteration':
                counter += 1
        return counter

    def on_remove_item(self, d=None, item=None):
        self.item_list.remove(item)

    def on_save(self):
        fname, _ = QFileDialog.getSaveFileName(
            self.ui, caption=u'Save Sequence', filter=u"Sequence (*.json)")
        if fname:
            self.save_to_file(fname)
        self.update_load_file_comboBox()
        return fname

    def save_to_file(self, fname):
        l = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            l.append(item.d)

        with open(fname, "w+") as f:
            f.write(json.dumps(l, indent=1))

    def on_load(self):
        fname, _ = QFileDialog.getOpenFileName(
            None, filter=u"Sequence (*.json)")
        if fname:
            self.load_file(fname)
        return fname

    def load_file(self, fname):
        self.listWidget.clear()
        with open(fname, "r") as f:
            lines = json.loads(f.read())
        for d in lines:
            self.add_listItem(d)
        self.link_iteration_items()

    def on_run_item(self):
        item = self.listWidget.currentItem()
        if item.d['type'] == 'measurement':
            print('WARNING measurement not supported without running threat')
            return (item, None)
        else:
            return (item, self.listWidget.currentItem().visit())

    def on_run_item_and_proceed(self):
        item, next_item = self.on_run_item()
        if next_item == None:
            row = self.listWidget.row(item)
            next_item = self.listWidget.item(row + 1)
        self.listWidget.setCurrentItem(next_item)

    def on_itemDoubleClicked(self, item):
        self.show_editor_checkBox.setChecked(True)
        d = item.d
        print('on_itemDoubleClicked')

    def link_iteration_items(self):
        start_iter_items = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.d['type'] == 'start-iteration':
                start_iter_items.append(item)
            if item.d['type'] == 'end-iteration':
                s_item = start_iter_items.pop()
                item.set_start_iteration_item(s_item)
                s_item.set_end_iteration_item(item)

        if len(start_iter_items) != 0:
            print("invalid list", start_iter_items)

    def run(self):
        self.link_iteration_items()
        N = self.listWidget.count()
        for i in range(N):
            self.listWidget.item(i).reset()

        for q in range(self.settings['cycles']):
            if self.interrupt_measurement_called:
                break

            # go through list
            j = 0
            while j < self.listWidget.count():

                while self.settings['paused']:
                    if self.interrupt_measurement_called:
                        break
                    time.sleep(0.03)

                # print('current j', j, N)
                self.current_item = item = self.listWidget.item(j)

                resp = item.visit()
                if resp != None:
                    # jump to item returned
                    j = self.listWidget.row(resp)
                else:
                    # go to next item
                    j += 1

                if self.interrupt_measurement_called:
                    break

    def post_run(self):
        self.current_item = None

    def update_display(self):
        from qtpy.QtCore import Qt
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item == self.current_item:
                item.setBackground(Qt.green)
            else:
                item.setBackground(Qt.white)

    def shutdown(self):
        os.system("shutdown /s /f /t 1")

    def restart(self):
        os.system("restart /r /f /t 1")

    def all_functions(self):
        funcs = [a for a in dir(self.app) if callable(
            getattr(self.app, a)) and a.startswith('__') is False]
        for m in self.app.measurements.values():
            for a in dir(m):
                try:
                    if callable(getattr(m, a)) and a.startswith('__') is False:
                        funcs.append(f'measurements.{m.name}.' + a)
                except:
                    pass
        for m in self.app.hardware.values():
            for a in dir(m):
                try:
                    if callable(getattr(m, a)) and a.startswith('__') is False:
                        funcs.append(f'hardware.{m.name}.' + a)
                except:
                    pass
        return funcs
