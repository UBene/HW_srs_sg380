'''
Created on Feb 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement
import pyqtgraph as pg
from ScopeFoundry import h5_io

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


def norm(x):
    x = np.array(x)
    return x / np.max(x)


class GenericSweeper(Measurement):

    name = 'generic_sweeper'
    
    def setup(self):
        self.range = self.settings.New_Range('sweep', include_sweep_type=True)
        self.settings.New('sweep_setting', str, choices=('a', 'b'))
        self.settings.New('collection_delay', float, initial=0.1)
        self.setup_prepare_sequences()
        
    def setup_prepare_sequences(self, sequences_dir='prepare_sequences'):
        _dir = os.path.abspath(os.path.join('.', sequences_dir))
        _prepare_sequences = [fname for fname in os.listdir(_dir) if fname.endswith('.json')]
        self.prepare_sequences = {}
        for fname in _prepare_sequences:
            measurement = fname.split('.')[0]
            set = self.settings.New(f'run_{measurement}_sequence',
                                    bool, initial=False)
            _fname = os.path.join(_dir, fname)
            self.prepare_sequences.update({measurement:{'setting':set,
                                                        'fname':_fname}})
            
    # def setup_default_data(self, _dir='default_data_attributs'):
            
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
        paths = self.get_list_of_settings()
        
        self.settings.sweep_setting.change_choice_list(paths)
        
        # self.x_lineEdit = QLineEdit()
        w = self.settings.sweep_setting.new_default_widget()
        completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        w.setCompleter(completer)
        x_layout.addWidget(w)
        x_settings_layout.addLayout(x_layout)
        x_settings_layout.addWidget(self.range.New_UI())
        
        # data settings
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel('data'))
        attrs = self.get_list_of_attributes()
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

        set_btn = QPushButton('set setting')
        set_btn.setToolTip('set sweep_quantity to equivalent value')
        y_settings_layout.addWidget(set_btn)
        set_btn.clicked.connect(self.on_go)

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
        # self.plot.setLogMode(True, True)
        self.plot.showGrid(True, True)
        self.display_ready = False
        self.line = self.plot.addLine(x=0, movable=True)

        # plot x
        plot_x_layout = QHBoxLayout()
        plot_x_layout.addWidget(QLabel('plot x'))
        self.plot_x_comboBox = QComboBox()
        plot_x_layout.addWidget(self.plot_x_comboBox)
        self.layout.addLayout(plot_x_layout)
        self.plot_x_comboBox.currentTextChanged.connect(self.on_plot_x_changed)
        
    def on_go(self):
        if 'stop' in self.settings['run_state']:
            x = self.line.getXPos()
            x_array = np.array(self.data[self.plot_x_data_name]['plot_values'])
            value = np.interp(x, x_array, self.range.sweep_array)
            sweep_setting = self.settings['sweep_setting']
            self.app.lq_path(sweep_setting).update_value(value)
            self.plot.setTitle(f'set {sweep_setting} to {value:2.2f}', color='y')
                    
    def run_prepare_measurement(self, name):
        if name in self.prepare_sequences:
            handle = self.prepare_sequences[name]
            if handle['setting'].value:
                sequencer = self.app.measurements['sequencer']
                sequencer.load_file(handle['fname'])
                self.start_nested_measure_and_wait(sequencer, nested_interrupt=False)
        
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
        self.plot.clear()
        self.ii = 0

        if self.settings['sweep_setting'] in ('', '0'):
            self.plot.setTitle('set a quantity to sweep', color='r')

        N = self.listWidget.count()        
        if N == 0:
            self.plot.setTitle('add a data attribute', color='r')
            
        self.task_list = [self.listWidget.item(i).text() for i in range(N)] 
        self.task_list.append(self.settings['sweep_setting'])
        
        # measurements to run and settings to read
        self._measurements = [] 
        self._settings_paths = []
        self.data = {}
        self.plot_lines = {}
        
        for text in self.task_list:
            print(text)
            if self.interrupt_measurement_called:
                break
            if text.startswith('measurements'):
                a, name, attr = text.split('.')

                if not name in self._measurements:
                    self._measurements.append(self.app.measurements[name])
                self.data.update({f'{name}__{attr}':{'plot_values':[],
                                                     'values':[],
                                                     'attr':text}})
                self.plot_lines.update({f'{name}__{attr}':self.plot.plot([1, 3, 2, 14],
                                                                         pen=pg.mkPen())})
                
            else:  # is a setting path
                print(text)
                a, name, setting = text.split('/')
                self._settings_paths.append(text)
                self.data.update({f'{name}__{setting}':{'plot_values':[],  # needed such
                                                        'values':[],
                                                        'attr':text}})
                self.plot_lines.update({f'{name}__{setting}':self.plot.plot([1, 3, 2, 4])})   
                
        self.plot_x_comboBox.clear()
        self.plot_x_comboBox.addItems(list(self.data.keys()))
        self.plot_x_data_name = f'{name}__{setting}'  # self.settings['sweep_setting'] was added last to task_list 
        self.plot.setTitle('running', color='g')
        
    def run(self):
        S = self.settings
        N = len(self.range.sweep_array)
        for ii, x in enumerate(self.range.sweep_array):
            if self.interrupt_measurement_called:
                break
            self.set_progress(100.0 * (ii + 1) / N)
            self.app.lq_path(self.settings['sweep_setting']).update_value(x)
            time.sleep(S['collection_delay'])

            # perform all measurements
            for measurement in self._measurements:
                if self.interrupt_measurement_called:
                    break
                
                self.run_prepare_measurement(measurement.name)
                self.start_nested_measure_and_wait(measurement, nested_interrupt=False)
                for k in self.data:
                    name, attr = k.split('__')
                    if name == measurement.name:
                        values = np.array(getattr(measurement, attr))
                        self.data[k]['values'].append(values)
                        self.data[k]['plot_values'].append(np.sum(values))

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
        self.h5_meas_group.attrs['sweep_quantity'] = self.settings['sweep_setting']
        self.h5_file.close()

    def post_run(self):
        self.plot.setTitle('finished', color='g')       
        self.plot.addItem(self.line)     

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
        print('update_display')
        self.line.setPos(3)
        print(self.line.getXPos(), self.line.angle)
        self.line.setPen('w')
        self.line.setVisible(True)
        self.line.setZValue(1000)
        print(self.line.__dict__)
        # self.line.setBrush('w')
            
    def get_list_of_attributes(self):
        attrs = []        
        for m in self.app.measurements.values():
            for a in dir(m):
                
                if not callable(getattr(m, a)) and\
                    a.startswith('__') == False and\
                    not a in ('settings', 'activation', 'name',
                              'log', 'gui', 'app', 'ui', 'display_update_period'
                              'display_update_timer', 'acq_thread',
                              'interrupt_measurement_called',
                              'operations', 'run_state', 't_start', 'end_state'):
                    attrs.append(f'measurements.{m.name}.' + a)
        return attrs 
    
    def get_list_of_settings(self):
        exclude = ('activation', 'connected', 'run_state', 'debug_mode')
        return [p for p in self.app.lq_paths_list() if not p.split('/')[-1] in exclude]
            
    def valid_type(self, x):

        def get_type(x):
            if type(x) in (np.array, dict):
                return type(x)
            if not hasattr(x, '__iter__'):
                return type(x)        
            elif len(x) == 0:
                return None
            else:
                return get_type(x[0])
            
        return get_type(x) in (int, float, np.array, bool)
    
    
if __name__ == '__main__':

    def get_type(x):
        if type(x) in (np.array, dict):
            return type(x)
        if not hasattr(x, '__iter__'):
            return type(x)        
        elif len(x) == 0:
            return None
        else:
            return get_type(x[0])     
        
    data = {}
    x = {'x':np.arange(10), 'y':np.cos(10)}
    
    if type(x) == dict:
        for k, v in x.items():
            data.update({k:[v]})
                
    x = {'x':np.arange(10), 'y':np.cos(10)}
    if type(x) == dict:
        for k, v in x.items():
            data.update({k:[v]})            
    print('data', data)
        
    # print(get_type( {'test': 1} ) in (int, float, np.array, bool))
    
