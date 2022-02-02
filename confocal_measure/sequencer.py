'''
Created on Sep 17, 2021

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path

import operator
from builtins import getattr
import time
import os
import json
import glob
import numpy as np
from qtpy.QtWidgets import QListWidget, QListWidgetItem, QCompleter, QComboBox, \
    QHBoxLayout, QPushButton, QGroupBox, QDoubleSpinBox, QVBoxLayout, QCheckBox, \
    QWidget, QSpinBox, QLineEdit, QFileDialog, QSpacerItem
from qtpy.QtCore import Qt
from PyQt5.Qt import QLabel


class Sequencer(Measurement):

    name = 'sequencer'

    def setup(self):
        self.settings.New('cycles', int, initial=1,
                          description='number of times the sequence is executed')
        self.settings.New('paused', bool, initial=False)
        
        self.iter_values = {}
        self.editors = {}
        self.letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
    def add_editor(self, type_name, on_add_func, layout, description=""):
        gb = QGroupBox(type_name.replace('_', '-'))
        gb.setToolTip(description)
        gb.setLayout(layout)
        self.editor_layout.addWidget(gb)
        
        add_btn = QPushButton('New')
        add_btn.setToolTip('CTRL+N')
        add_btn.setFixedWidth(30)
        layout.addWidget(add_btn)
        add_btn.clicked.connect(on_add_func)
        
        if type_name == 'iteration':
            item_type = 'start-iteration'
        else:
            item_type = type_name
            
        def on_replace_func():
            item = self.listWidget.currentItem()
            if item.d['type'] == 'end-iteration':
                item = item.start_iteration_item
            if item.d['type'] == item_type:
                d = on_add_func(True)
                item.update_d(d)
            else:            
                row = self.listWidget.currentRow()
                self.on_remove_item(item=item)
                self.listWidget.setCurrentRow(row - 1)
                on_add_func()
                
        replace_btn = QPushButton('Replace')
        replace_btn.setFixedWidth(50)
        replace_btn.setToolTip('CTRL+R')
        layout.addWidget(replace_btn)
        replace_btn.clicked.connect(on_replace_func)                
                
        self.editors.update({type_name:{'groubBox': gb,
                                   'on_add_func': on_add_func,
                                   'on_replace_func': on_replace_func,
                                   'add_pushButton':add_btn,
                                   'replace_pushButton':replace_btn,
                                   'layout':layout,
                                   'description':description}
                                    })
        
        return gb
        
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
        self.load_file_comboBox.currentTextChanged.connect(self.on_load_file_comboBox_changed)
        self.layout.addWidget(self.load_file_comboBox)

        # list widget
        self.listWidget = QListWidget()
        self.listWidget.setDefaultDropAction(Qt.MoveAction)
        self.listWidget.setDragDropMode(QListWidget.DragDrop)
        self.layout.addWidget(self.listWidget)
        self.listWidget.itemDoubleClicked.connect(self.on_itemDoubleClicked)

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
        self.editor_widget = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_widget)
        self.show_editor_checkBox.stateChanged.connect(self.editor_widget.setVisible)
        self.show_editor_checkBox.setChecked(True)
        self.layout.addWidget(self.editor_widget)
        
        # # setting-update
        gb = self.add_editor('update-setting', self.on_add_setting, QHBoxLayout(),
                             description='''update a setting with value, a setting, 
                             read_from_hardware or __<iteration letter>''')
        setting_layout = gb.layout()
        gb.setTitle('update-setting && read_from_hardwater')
        paths = self.app.lq_paths_list()
        self.setting_comboBox = QComboBox()
        self.setting_comboBox.setEditable(True)
        self.setting_comboBox.addItems(paths)
        self.setting_comboBox.setToolTip('setting to update')
        self.completer = completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_comboBox.setCompleter(completer)
        setting_layout.addWidget(self.setting_comboBox)
        self.setting_lineEdit = QLineEdit()
        _paths = paths + ["read_from_hardware", "True", "False", "__A", "__B", "__C", "__D"]
        completer = QCompleter(_paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setting_lineEdit.setCompleter(completer)
        self.setting_lineEdit.setToolTip('''value used to update. Can be a value, a setting, 
                                            'read_from_hardware' or '__<iteration letter>' ''')
        setting_layout.addWidget(self.setting_lineEdit)

        # # measurement
        gb = self.add_editor('measurement', self.on_add_measure, QHBoxLayout(),
                             description='a scopeFoundry Measurement')
        measure_layout = gb.layout()
        measurements = self.app.measurements.keys()
        self.measure_comboBox = QComboBox()
        self.measure_comboBox.setEditable(True)
        self.measure_comboBox.addItems(measurements)
        self.completer = completer = QCompleter(measurements)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.measure_comboBox.setCompleter(completer)
        measure_layout.addWidget(self.measure_comboBox)
        self.measure_spinBox = QSpinBox()
        self.measure_spinBox.setValue(1)
        self.measure_spinBox.setToolTip('number of repeats')
        measure_layout.addWidget(self.measure_spinBox)

        # # wait-until
        gb = self.add_editor('wait-until', self.on_add_wait_until, QHBoxLayout(),
                             description='wait until condition is met')
        wait_until_layout = gb.layout()
        self.wait_until_comboBox = QComboBox()
        self.wait_until_comboBox.setEditable(True)
        self.wait_until_comboBox.addItems(paths)
        self.wait_until_comboBox.setToolTip('setting')
        self.completer = completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.wait_until_comboBox.setCompleter(completer)
        wait_until_layout.addWidget(self.wait_until_comboBox)
        self.wait_until_operator_comboBox = QComboBox()
        self.wait_until_operator_comboBox.addItems(['=', '<', '>'])
        wait_until_layout.addWidget(self.wait_until_operator_comboBox)
        self.wait_until_lineEdit = QLineEdit()
        self.wait_until_lineEdit.setToolTip('wait until setting reaches this value')
        wait_until_layout.addWidget(self.wait_until_lineEdit)

        # # timeout
        gb = self.add_editor('timeout', self.on_add_time_out, QHBoxLayout(),
                             description='wait for a specified time')
        time_out_layout = gb.layout()
        self.time_out_doubleSpinBox = QDoubleSpinBox()
        self.time_out_doubleSpinBox.setValue(0.1)
        self.time_out_doubleSpinBox.setToolTip('time-out in sec')
        self.time_out_doubleSpinBox.setMaximum(1e6)
        self.time_out_doubleSpinBox.setDecimals(3)
        time_out_layout.addWidget(self.time_out_doubleSpinBox)

        # # function execute              
        gb = self.add_editor('function', self.on_add_function_execute, QHBoxLayout(),
                             description='eval a function')
        function_execute_layout = gb.layout()      
        self.function_lineEdit = QLineEdit()
        completer = QCompleter(self.all_functions())
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.function_lineEdit.setCompleter(completer)
        self.function_lineEdit.setToolTip('path to a function')
        self.function_args_lineEdit = QLineEdit()
        self.function_args_lineEdit.setToolTip('function arguments')
        function_execute_layout.addWidget(self.function_lineEdit)
        function_execute_layout.addWidget(self.function_args_lineEdit)

        # # iteration
        gb = self.add_editor('iteration', self.on_add_iteration, QHBoxLayout(),
                             description='a setting is iterated over a range of values')
        iteration_layout = gb.layout()   
        self.iteration_comboBox = QComboBox()
        self.iteration_comboBox.setEditable(True)
        self.iteration_comboBox.addItems(paths)
        self.iteration_comboBox.setToolTip('setting')
        self.completer = completer = QCompleter(paths)
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
        
        # # interrupt-if
        gb = self.add_editor('interrupt-if', self.on_add_interrupt_if, QHBoxLayout(),
                             description=f'interrupt {self.name} if a condition is met')
        interrupt_if_layout = gb.layout()   
        self.interrupt_if_comboBox = QComboBox()
        self.interrupt_if_comboBox.setEditable(True)
        self.interrupt_if_comboBox.addItems(paths)
        self.interrupt_if_comboBox.setToolTip('setting')
        self.completer = completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.interrupt_if_comboBox.setCompleter(completer)
        interrupt_if_layout.addWidget(self.interrupt_if_comboBox)
        self.interrupt_if_operator_comboBox = QComboBox()
        self.interrupt_if_operator_comboBox.addItems(['=', '<', '>'])
        interrupt_if_layout.addWidget(self.interrupt_if_operator_comboBox)
        self.interrupt_if_lineEdit = QLineEdit()
        interrupt_if_layout.addWidget(self.interrupt_if_lineEdit)
        
        # # pause
        gb = self.add_editor('pause', self.on_add_pause, QHBoxLayout(),
                             description=f'{self.name} pauses - click resume')
        self.pause_spacer = QLabel()
        gb.layout().addWidget(self.pause_spacer)
        
        # key events
        self.listWidget.keyReleaseEvent = self._keyReleaseEvent
        self.editor_widget.keyPressEvent = self._editorKeyPressEvent
    
    def _keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.on_remove_item()
        if event.key() == Qt.Key_Space:
            self.on_run_item_and_proceed()
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            print(event.key())
            item = self.listWidget.currentItem()
            self.on_itemDoubleClicked(item)
            
    def _editorKeyPressEvent(self, event):
        # find editor with focused widget
        if event.modifiers() & Qt.ControlModifier and event.key() in (Qt.Key_R, Qt.Key_N):
            fw = self.editor_widget.focusWidget()
            for key, val in self.editors.items():
                for item in val['groubBox'].children():
                    if fw == item:
                        type_name = key                
                        if event.key() == Qt.Key_R:
                            self.editors[type_name]['on_replace_func']()
                        if event.key() == Qt.Key_N:
                            self.editors[type_name]['on_add_func']()   
        else:
            if event.key() in (Qt.Key_F1,):
                self.listWidget.setFocus()
                
    def update_load_file_comboBox(self):
        fnames = glob.glob(glob.os.getcwd() + '\..\..\**/*.json', recursive=True)
        index0 = self.load_file_comboBox.currentIndex()
        self.load_file_comboBox.clear()
        self.seq_fnames = {}
        for fname in fnames:
            abbrev_fname = '\\'.join(fname.split('\\')[-2:])
            self.seq_fnames.update({abbrev_fname:fname})
        self.load_file_comboBox.addItems(list(self.seq_fnames.keys()))
        self.load_file_comboBox.setCurrentIndex(index0)
        
    def on_load_file_comboBox_changed(self, fname):
        self.load_file(self.seq_fnames[fname])

    def on_add_setting(self, ignore_add_listItem=False):
        path = self.setting_comboBox.currentText()
        val = self.setting_lineEdit.text()
        if val == 'read_from_hardware':
            d = {'type':'read_from_hardware', 'setting':path}
        else:
            d = {'type':'update-setting', 'setting':path, 'value':val}
        if not ignore_add_listItem:
            self.add_listItem(d)
        return d        
    
    def on_add_wait_until(self, ignore_add_listItem=False):
        path = self.wait_until_comboBox.currentText()
        o = self.wait_until_operator_comboBox.currentText()
        val = self.wait_until_lineEdit.text()
        d = {'type':'wait-until', 'setting':path, 'operator':o, 'value':val}
        if not ignore_add_listItem:
            self.add_listItem(d)
        return d
    
    def on_add_time_out(self, ignore_add_listItem=False):
        t = self.time_out_doubleSpinBox.value()
        d = {'type':'timeout', 'time':t}
        if not ignore_add_listItem:
            self.add_listItem(d)
        return d
    
    def on_add_measure(self, ignore_add_listItem=False):
        k = self.measure_comboBox.currentText()
        reps = self.measure_spinBox.value()
        d = {'type':'measurement', 'measurement':k, 'repetitions':reps}
        if not ignore_add_listItem:
            self.add_listItem(d)
        return d

    def on_add_function_execute(self, ignore_add_listItem=False):
        f = self.function_lineEdit.text()
        args = self.function_args_lineEdit.text()
        d = {'type':'function', 'function':f, 'args':args}
        if not ignore_add_listItem:
            self.add_listItem(d)
        return d    

    def on_add_iteration(self, ignore_add_listItem=False):   
        path = self.iteration_comboBox.currentText() 
        start = self.iteration_start_doubleSpinBox.value()
        stop = self.iteration_stop_doubleSpinBox.value()
        step = self.iteration_step_doubleSpinBox.value()
        values = list(np.arange(start, stop, step)) 
        d = {'type':'start-iteration', 'setting':path, 'values':values}
        if not ignore_add_listItem:
            self.add_listItem(d)
            self.add_listItem({'type':'end-iteration'})        
            self.link_iteration_items()
        return d        

    def on_add_interrupt_if(self, ignore_add_listItem=False):
        path = self.interrupt_if_comboBox.currentText()
        o = self.interrupt_if_operator_comboBox.currentText()
        val = self.interrupt_if_lineEdit.text()
        d = {'type':'interrupt-if', 'setting':path, 'operator':o, 'value':val}
        if not ignore_add_listItem:
            self.add_listItem(d)
        return d 
    
    def on_add_pause(self, ignore_add_listItem=False):
        d = {'type':'pause', 'info': "click resume to continue"}
        print('pause')
        if not ignore_add_listItem:
            self.add_listItem(d)
        return d         
    
    def add_listItem(self, d, text=None, row=None):
        if row == None:
            row = self.listWidget.currentIndex().row()
        if d['type'] == 'start-iteration':
            iter_id = self.letters[self.iterations_count]
            item = StartIterationListWidgetItem(self.app, self, d, iter_id, text)
        elif d['type'] == 'end-iteration':
            item = EndIterationListWidgetItem(self.app, self, d, text)
        else:
            item = ListItem(self.app, self, d, text)
            # item.setToolTip(self.editors[d['type']]["description"])
        self.listWidget.insertItem(row + 1, item)
        self.listWidget.setCurrentRow(row + 1)
    
    @property
    def iterations_count(self):
        counter = 0
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)            
            if item.d['type'] == 'start-iteration':
                counter += 1
        return counter

    def on_remove_item(self, d=None, item=None):        
        if item == None:
            item = self.listWidget.item(self.listWidget.currentRow())            
        self.listWidget.takeItem(self.listWidget.row(item))
        for s in ['start_iteration_item', 'end_iteration_item']:
            try:
                item2 = self.listWidget.takeItem(self.listWidget.row(getattr(item, s)))
                del item2
            except:
                pass
        del item

    def on_save(self):
        fname, _ = QFileDialog.getSaveFileName(self.ui, caption=u'Save Sequence', filter=u"Sequence (*.json)")
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
        fname, _ = QFileDialog.getOpenFileName(None, filter=u"Sequence (*.json)")
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
        
        if d['type'] == 'update-setting':
            self.setting_comboBox.setCurrentText(d['setting'])
            self.setting_lineEdit.setText(d['value'])
            self.setting_lineEdit.selectAll()
            self.setting_lineEdit.setFocus()
            
        if d['type'] == 'read_from_hardware':
            print(d['setting'], type(d['setting']))
            self.setting_comboBox.setCurrentText(d['setting'])
            self.setting_lineEdit.setText('read_from_hardware')
            self.setting_comboBox.setFocus()
            
        if d['type'] == 'wait-until':
            self.wait_until_comboBox.setCurrentText(d['setting'])
            self.wait_until_operator_comboBox.setCurrentText(d['operator'])
            self.wait_until_lineEdit.setText(d['value'])
            self.wait_until_lineEdit.selectAll()
            self.wait_until_lineEdit.setFocus()

        if d['type'] == 'measurement':
            self.measure_comboBox.setCurrentText(d['measurement'])
            self.measure_spinBox.setValue(d['repetitions'])
            self.measure_comboBox.setFocus()

        if d['type'] == 'timeout':
            self.time_out_doubleSpinBox.setValue(d['time'])
            self.time_out_doubleSpinBox.selectAll()
            self.time_out_doubleSpinBox.setFocus()

        if d['type'] == 'function':
            self.function_lineEdit.setText(d['function'])
            self.function_args_lineEdit.setText(d['args'])
            self.function_args_lineEdit.selectAll()
            
        if 'iteration' in d['type']:
            self.iteration_start_doubleSpinBox.setValue(d['values'][0])
            step = d['values'][1] - d['values'][0]
            self.iteration_step_doubleSpinBox.setValue(step)
            self.iteration_stop_doubleSpinBox.setValue(d['values'][-1] + step)
            self.iteration_start_doubleSpinBox.selectAll()
            self.iteration_start_doubleSpinBox.setFocus()

        if d['type'] == 'interrupt-if':
            self.interrupt_if_comboBox.setCurrentText(d['setting'])
            self.interrupt_if_operator_comboBox.setCurrentText(d['operator'])
            self.interrupt_if_lineEdit.setText(d['value'])
            self.interrupt_if_lineEdit.selectAll()
            self.interrupt_if_lineEdit.setFocus()        
            
        if d['type'] == 'pause':
            self.pause_spacer.setFocus()
            
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
        funcs = [a for a in dir(self.app) if callable(getattr(self.app, a)) and a.startswith('__') is False]
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
        
        
class ListItem(QListWidgetItem):

    # Future Plans: make a ListItem for each type
    def __init__(self, app, measure, d={'type':'undefined'}, text=None):    
        QListWidgetItem.__init__(self)
        self.app = app
        self.measure = measure
        self.d = d
        self.update_d(d)
        
    def update_d(self, d):
        self.d.update(d)
        self.update_appearance()
        
    def update_appearance(self, text=None):
        if text == None:
            x = [f'{val}' for key, val in self.d.items() if key != 'type']
            text = f"{self.d['type']}: {' '.join(x)}" 
        self.setText(text)
        return text
        
    def visit(self):
        d = self.d
        if d['type'] == 'update-setting':
            v = d['value']                        
            try:
                v = self.app.lq_path(v).val
            except:
                pass
            
            if isinstance(v, str):
                if '__' in v:        
                    letter = v[v.find('__') + 2]
                    v = self.measure.iter_values[letter]
            self.app.lq_path(d['setting']).update_value(v)
            
        if d['type'] == 'read_from_hardware':
            self.app.lq_path(d['setting']).read_from_hardware()

        if d['type'] == 'measurement':
            m = self.app.measurements[d['measurement']]
            for i in range(d['repetitions']):
                try:
                    self.measure.start_nested_measure_and_wait(m, nested_interrupt=False)
                except:
                    print(self.measure, 'delegated', m.name, 'failed')

        if d['type'] == 'wait-until':
            relate = {'=':operator.eq, '>':operator.gt, '<':operator.lt}[d['operator']]
            lq = self.app.lq_path(d['setting'])
            val = lq.coerce_to_type(d['value'])
            while True:                        
                if relate(lq.val, val) or self.measure.interrupt_measurement_called:
                    break
                time.sleep(0.05)

        if d['type'] == 'timeout':
            t0 = time.time()
            while True:
                dt = time.time() - t0
                if self.measure.interrupt_measurement_called or dt > d['time']:
                    break
                time.sleep(0.05)
            
        if d['type'] == 'function':
            s = 'self.app.' + d['function'] + '(' + d['args'] + ')'
            print(s)
            print(eval(s))

        if d['type'] == 'interrupt-if':
            relate = {'=':operator.eq, '>':operator.gt, '<':operator.lt}[d['operator']]
            lq = self.app.lq_path(d['setting'])
            val = lq.coerce_to_type(d['value'])
            if relate(lq.val, val):
                self.measure.interrupt()

        if d['type'] == 'pause':
            self.measure.settings['paused'] = True

        time.sleep(0.05)
    
    def reset(self):
        pass
    
        
class StartIterationListWidgetItem(ListItem):
    
    def __init__(self, app, measure, d, iter_id=None, text=None):    
        self.iter_id = iter_id
        ListItem.__init__(self, app=app, measure=measure, d=d, text=text)
        self.reset()
        
    def update_d(self, d):
        ListItem.update_d(self, d)
        self.lq = self.app.lq_path(d['setting'])
        self.values = d['values']
        
    def update_appearance(self, text=None):
        text = ListItem.update_appearance(self, text=text)
        self.setText(f'__{self.iter_id} ' + text)
                
    def visit(self):
        self.idx += 1
        if self.idx == len(self.values) - 1: 
            # next time end-iteration is visited the loop breaks
            self.end_iteration_item.break_next = True
        self.lq.update_value(self.values[self.idx])
        self.update_text()
        self.measure.iter_values.update({self.iter_id:self.values[self.idx]})
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

    
class EndIterationListWidgetItem(ListItem):

    def __init__(self, app, measure, d, text=None):
        self.iter_id = None
        ListItem.__init__(self, app=app, measure=measure, d=d, text=text)
        self.break_next = False
        
    def update_appearance(self, text=None):
        text = ListItem.update_appearance(self, text=text)
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
            pct = 100.0 * (self.start_iteration_item.idx + 1) / (len(self.start_iteration_item.values))
            self.setText(text + f' - {pct: 1.0f} %')
        except:
            pass

    
class SweepSequencer(Sequencer):
    
    name = 'sweep_sequencer'
    
    def setup(self):
        Sequencer.setup(self)
        self.range = self.settings.New_Range('range', include_sweep_type=True, initials=[67, 410, 10],
                            description='''use measurement/sweep_sequencer/current_range_value to 
                                           update the setting you want to sweep''',
                            spinbox_decimals=5)
        self.settings.New('current_range_value', ro=True)
        self.settings.New('ignore_sweep', bool, initial=False)
        
    def setup_figure(self):
        Sequencer.setup_figure(self)
        layout = QHBoxLayout()
        layout.addWidget(self.range.New_UI())
        layout.addWidget(self.settings.New_UI(['current_range_value', 'ignore_sweep']))
        self.layout.insertLayout(1, layout)
        self.setting_lineEdit.setText("measurement/sweep_sequencer/current_range_value")
                
    def run(self):
        if self.settings['ignore_sweep']:
            Sequencer.run(self)
        else:
            for i, x in enumerate(self.range.sweep_array):
                if self.interrupt_measurement_called:
                    break
                self.settings['current_range_value'] = x
                # print(self.name, 'current_range_value', x)
                self.set_progress(100.0 * i / len(self.range.sweep_array))
                Sequencer.run(self)
