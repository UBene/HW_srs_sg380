'''
Created on Feb 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import load_qt_ui_file, sibling_path
import pyqtgraph as pg
from ScopeFoundry import h5_io

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
from PyQt5.Qt import QLabel, QLayout
import attr
from copy import copy


def norm(x):
    x = np.array(x)
    return x / np.max(x)


class GenericSweeper(Measurement):

    name = 'generic_sweeper'
    
    def setup(self):
        self.range = self.settings.New_Range('sweep', include_sweep_type=True)
        self.settings.New('collection_delay', float, initial=0.1)
        self.add_operation('on_add_item', self.on_add_item)
    
    def setup_figure(self):
        self.ui = QWidget()
        self.layout = QVBoxLayout(self.ui)
        
        # Start Stop
        self.layout.addWidget(self.settings.activation.new_pushButton())

        # Layouts
        # x_settings_layout | y_settings_layout | list_layout
        # --------------------
        # plot_layout
        settings_layout = QHBoxLayout()
        settings_layout.setSizeConstraint(QLayout.SetMinimumSize)
        x_settings_layout = QVBoxLayout()
        y_settings_layout = QVBoxLayout()
        list_layout = QVBoxLayout()
        settings_layout.addLayout(x_settings_layout)
        settings_layout.addLayout(y_settings_layout)
        settings_layout.addLayout(list_layout)
        self.layout.addLayout(settings_layout)

        # x_settings
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel('sweep_quantity'))
        paths = self.app.lq_paths_list()
        self.x_lineEdit = QLineEdit()
        completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.x_lineEdit.setCompleter(completer)
        x_layout.addWidget(self.x_lineEdit)
        x_settings_layout.addLayout(x_layout)
        
        x_settings_layout.addWidget(self.range.New_UI())
        
        # data settings
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel('data'))
        attrs = []        
        for m in self.app.measurements.values():
            for a in dir(m):
                try:
                    if not callable(getattr(m, a)) and\
                        a.startswith('__') == False and\
                        not a in ('settings', 'activation', 'name', 'log', 'gui'):
                        attrs.append(f'measurements.{m.name}.' + a)
                except:
                    pass
        self.y_lineEdit = QLineEdit()
        completer = QCompleter(attrs + paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.y_lineEdit.setCompleter(completer)
        y_layout.addWidget(self.y_lineEdit)
        y_settings_layout.addLayout(y_layout)

        add_btn = QPushButton('add')
        y_settings_layout.addWidget(add_btn)
        add_btn.clicked.connect(self.on_add_item)
        
        remove_btn = QPushButton('remove')
        y_settings_layout.addWidget(remove_btn)
        remove_btn.clicked.connect(self.on_remove_item)   

        # list 
        self.listWidget = QListWidget()
        self.listWidget.setDefaultDropAction(Qt.MoveAction)
        self.listWidget.setDragDropMode(QListWidget.DragDrop)
        list_layout.addWidget(self.listWidget)
        # self.listWidget.itemDoubleClicked.connect(self.on_itemDoubleClicked)
        self.listWidget.setMaximumHeight(200)
        
        # plot
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title="generic sweep")
        self.plot.setLogMode(True, True)
        self.plot.showGrid(True, True)
        self.display_ready = False
        #self.line = self.plot.addLine(x=0, movable=True)
        
        

        # plot x
        plot_x_layout = QHBoxLayout()
        plot_x_layout.addWidget(QLabel('plot x'))
        self.plot_x_comboBox = QComboBox()
        plot_x_layout.addWidget(self.plot_x_comboBox)
        self.layout.addLayout(plot_x_layout)
        self.plot_x_comboBox.currentTextChanged.connect(self.on_plot_x_changed)
        
        #go_btn = QPushButton('go')
        #go_btn.setToolTip('set sweep_quantity to equivalent value')
        #y_settings_layout.addWidget(go_btn)
        #add_btn.clicked.connect(self.on_go)
        
    def on_plot_x_changed(self, text):
        self.plot_x_data_name = text
        self.update_display()
                
    def on_add_item(self):
        task = self.y_lineEdit.text()
        self.listWidget.addItem(QListWidgetItem(task))
        
    def on_remove_item(self): 
        item = self.listWidget.item(self.listWidget.currentRow())            
        self.listWidget.takeItem(self.listWidget.row(item))
        del item
        
    def pre_run(self): 
        self.display_ready = False
        self.ii = 0
        self.plot.clear()
        
        # list task
        self.sweep_quantity = self.x_lineEdit.text()
        print('sweep_quantity', repr(self.sweep_quantity))
        if self.sweep_quantity == '':
            self.plot.setTitle('set a quantity to sweep', color='r')

        N = self.listWidget.count()        
        if N == 0:
            self.plot.setTitle('add a data attribute', color='r')
            
        self.task_list = [self.listWidget.item(i).text() for i in range(N)] 
        self.task_list.append(self.sweep_quantity)
        print(self.name, 'saving quantities')
        print(self.task_list)
        
        # measurements to run and settings to read
        self._measurements = [] 
        self._settings_paths = []
        self.data = {}
        self.plot_lines = {}
        for text in self.task_list:
            if self.interrupt_measurement_called:
                break
            if text.startswith('measurements'):
                a, name, attr = text.split('.')
                if not name in self._measurements:
                    self._measurements.append(self.app.measurements[name])
                self.data.update({f'{name}__{attr}':{'plot_values':[],
                                                    'values':[]}})
                self.plot_lines.update({f'{name}__{attr}':self.plot.plot([1, 3, 2, 4],
                                                                         pen=pg.mkPen())})
            else:  # is a setting path
                a, name, setting = text.split('/')
                self._settings_paths.append(text)
                self.data.update({f'{name}__{setting}':{'plot_values':[],  # needed sutch
                                                    'values':[]}})
                self.plot_lines.update({f'{name}__{setting}':self.plot.plot([1, 3, 2, 4])})   
                
        self.plot_x_comboBox.clear()
        self.plot_x_comboBox.addItems(list(self.data.keys()))
        self.plot_x_data_name = f'{name}__{setting}'  # self.sweep_quantity was added last to task_list 
        self.plot.setTitle('running', color='g')
        
        
    def run(self):
        S = self.settings
        N = len(self.range.sweep_array)
        for ii, x in enumerate(self.range.sweep_array):
            if self.interrupt_measurement_called:
                break
            self.set_progress(100.0 * (ii + 1) / N)
            self.app.lq_path(self.sweep_quantity).update_value(x)
            time.sleep(S['collection_delay'])

            # perform all measurements
            for measurement in self._measurements:
                if self.interrupt_measurement_called:
                    break
                self.start_nested_measure_and_wait(measurement, nested_interrupt=False)
                for d in self.data:
                    print()
                    name, attr = d.split('__',)
                    if name == measurement.name:
                        values = np.array(getattr(measurement, attr))
                        print(attr, values)

                        self.data[d]['values'].append(values)
                        self.data[d]['plot_values'].append(np.sum(values))

            # read settings                            
            for path in self._settings_paths:
                value = self.app.lq_path(path).read_from_hardware()
                a, name, setting = path.split('/')
                self.data[f'{name}__{setting}']['plot_values'].append(value)
                self.data[f'{name}__{setting}']['values'].append(value)
                
            if ii == 0:
                self.display_ready = True
            self.ii = ii
            
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)
        for k, v in self.data.items():
            self.h5_meas_group[str(k) + '_plot_values'] = v['plot_values']
            self.h5_meas_group[str(k)] = v['values']
        self.h5_meas_group['sweep_array'] = self.range.sweep_array
        self.h5_meas_group.attrs['sweep_quantity'] = self.sweep_quantity
        self.h5_file.close()
        self.plot.setTitle('finished', color='g')
        
        
        

    def update_display(self):
        if self.display_ready:
            ii = self.ii + 1
            x = self.data[self.plot_x_data_name]['plot_values'][:ii]
            for k in self.data:
                if k != self.plot_x_data_name:
                    y = norm(self.data[k]['plot_values'][:ii])
                    self.plot_lines[k].setData(x, y)
                else:
                    self.plot_lines[k].clear()
                    
                    
    #def on_go(self):
    #    print(self.line.pos())
    
