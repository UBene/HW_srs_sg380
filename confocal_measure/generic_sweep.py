'''
Created on Feb 19, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement
import pyqtgraph as pg
from ScopeFoundry import h5_io
import time
import os
import numpy as np
from qtpy.QtWidgets import QListWidget, QListWidgetItem, QCompleter, QComboBox, \
    QHBoxLayout, QPushButton, QVBoxLayout, QWidget, QLineEdit, QGroupBox, QLabel
from qtpy import QtCore

    
def norm(x):
    x = np.array(x)
    x -= x.min() * 0.99
    return x / np.max(x)


class GenericSweeper(Measurement):

    name = 'generic_sweeper'
    
    def setup(self):
        self.range = self.settings.New_Range('sweep', include_sweep_type=True)
        self.settings.New('sweep_setting', str, choices=('a', 'b'))
        self.settings.New('collection_delay', float, initial=0.1)
        self.settings.New('polar_plot', bool, initial=False)
        self.settings.New('compress', bool, initial=False,
                          description='guesses data duplicates and only stores one.')
        self.setup_prepare_sequences_settings()
        self.setup_collect_measurement()
        
    def setup_prepare_sequences_settings(self, sequences_dir='prepare_sequences'):
        '''checks *sequences_dir* for sequences that should be run before a measurements. 
            The sequence file must have the same name as measurement'''
        try:
            _dir = os.path.abspath(os.path.join('.', sequences_dir))
            _prepare_sequences = [fname for fname in os.listdir(_dir) if fname.endswith('.json')]
            self.prepare_sequences = {}
            for fname in _prepare_sequences:
                name = fname.split('.')[0]
                setting = self.settings.New(f'run_{name}_sequence',
                                        bool, initial=False,
                                        description=f'runs {sequences_dir}/{name}.json sequence before running {name}')
                _fname = os.path.join(_dir, fname)
                self.prepare_sequences.update({name:{'setting':setting,
                                                    'fname':_fname}})
        except FileNotFoundError:
            pass
        
    def run_prepare_sequence(self, name):
        if name in self.prepare_sequences:
            handle = self.prepare_sequences[name]
            if handle['setting'].value:
                sequencer = self.app.measurements['sequencer']
                sequencer.load_file(handle['fname'])
                self.start_nested_measure_and_wait(sequencer, nested_interrupt=False)
            
    def setup_collect_measurement(self):
        '''checks if measurements of the app has a data (dictionary) 
            attribute and if so it adds a measurement'''
        self.includes_measurements = []
        for m in self.app.measurements.values():
            if hasattr(m, 'data'):
                self.settings.New(m.name, bool, initial=False,
                        description=f'runs {m.name} and save its .data dict at each iteration')
                self.includes_measurements.append(m.name)
            
    def setup_figure(self):
        self.ui = QWidget()
        self.layout = QVBoxLayout(self.ui)
        
        # Start Stop
        self.layout.addWidget(self.settings.activation.new_pushButton())

        # # Generate settings Layout
        # settings_layout
        # sweep_settings | collect | additional_layout
        #                             _additional_layout
        #                              y_settings_layout | list_layout
        settings_layout = QHBoxLayout()
        self.layout.addLayout(settings_layout)
        
        sweep_settings_groubBox = QGroupBox('sweep settings')
        sweep_settings_layout = QVBoxLayout()
        sweep_settings_groubBox.setLayout(sweep_settings_layout)
        collect_groubBox = QGroupBox('measurements to do')
        collect_layout = QVBoxLayout()        
        collect_groubBox.setLayout(collect_layout)
        collect_groubBox.setToolTip('''measurements with a <i>data</i> dictionary will show up here. 
                                    If checked the measurement is run and its data is 
                                    collected at every iteration and saved''')
        additional_groupBox = QGroupBox('additional attributes && settings to save')
        additional_layout = QVBoxLayout()
        additional_groupBox.setLayout(additional_layout)
        additional_groupBox.setMaximumHeight(280)
            
        for gb in [sweep_settings_groubBox, collect_groubBox, additional_groupBox]: 
            settings_layout.addWidget(gb)

        # # Fill settings layouts
        # sweep_settings
        paths = self.get_list_of_settings()
        self.settings.sweep_setting.change_choice_list(paths)
        w = self.settings.sweep_setting.new_default_widget()
        completer = QCompleter(paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        w.setCompleter(completer)
        sweep_settings_layout.addWidget(w)
        sweep_settings_layout.addWidget(self.range.New_UI())

        # collect layout
        w = self.settings.New_UI(self.includes_measurements)
        collect_layout.addWidget(w)
        
        # additional_layout
        attrs = self.get_list_of_attributes()
        self.y_lineEdit = QLineEdit()
        completer = QCompleter(attrs + paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.y_lineEdit.setCompleter(completer)
        additional_layout.addWidget(self.y_lineEdit)
        
        y_settings_layout = QVBoxLayout()
        list_layout = QVBoxLayout()
        _additional_layout = QHBoxLayout()
        for l in [y_settings_layout, list_layout]:
            _additional_layout.addLayout(l)      
        additional_layout.addLayout(_additional_layout)  
        
        add_btn = QPushButton('add -->')
        y_settings_layout.addWidget(add_btn)
        add_btn.clicked.connect(self.on_add_additional_attr_item)
        
        remove_btn = QPushButton('remove')
        y_settings_layout.addWidget(remove_btn)
        remove_btn.clicked.connect(self.on_remove_additional_attr_item)   

        # list 
        self.listWidget = QListWidget()
        self.listWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.listWidget.setDragDropMode(QListWidget.DragDrop)
        list_layout.addWidget(self.listWidget)
        self.listWidget.keyReleaseEvent = self._keyReleaseEvent        
        
        # plot
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot(title="generic sweep")
        self.plot.showGrid(True, True)
        self.display_ready = False
        self.set_sweep_setting = self.plot.addLine(x=0, movable=True, pen='y')

        # plot x
        plot_x_layout = QHBoxLayout()
        plot_x_layout.addWidget(QLabel('plot x'))
        self.plot_x_comboBox = QComboBox()
        plot_x_layout.addWidget(self.plot_x_comboBox)
        self.layout.addLayout(plot_x_layout)
        self.plot_x_comboBox.currentTextChanged.connect(self.on_plot_x_changed)
        plot_x_layout.addWidget(self.settings.polar_plot.new_default_widget())
        
        set_btn = QPushButton('set sweep setting')
        set_btn.setToolTip('set <b>sweep_quantity</b> to equivalent value of yellow')
        plot_x_layout.addWidget(set_btn)
        set_btn.clicked.connect(self.on_set_sweep_setting)
        
    def _keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.on_remove_additional_attr_item()
        
    def on_set_sweep_setting(self):
        if 'stop' in self.settings['run_state']:
            x = self.set_sweep_setting.getXPos()
            x_array = np.array(self.data_sets[self.plot_x_data_name]['plot_values'])
            value = np.interp(x, x_array, self.range.sweep_array)
            sweep_setting = self.settings['sweep_setting']
            self.app.lq_path(sweep_setting).update_value(value)
            self.plot.setTitle(f'set {sweep_setting} to {value:2.2f}', color='y')
        
    def on_plot_x_changed(self, text):
        self.plot_x_data_name = text
        self.update_display()
                
    def on_add_additional_attr_item(self):
        data_input = self.y_lineEdit.text()
        self.listWidget.addItem(QListWidgetItem(data_input))
        
    def on_remove_additional_attr_item(self): 
        item = self.listWidget.item(self.listWidget.currentRow())            
        self.listWidget.takeItem(self.listWidget.row(item))
        del item
        
    def make_data_input_list(self): 
        self.data_input_list = []  
        # checked measurements
        for name in self.includes_measurements:
            data_input = f'measurements.{name}.data'
            self.data_input_list.append(data_input)
        self.data_input_list.append(self.settings['sweep_setting'])
        # additional data_input list      
        N = self.listWidget.count()        
        for i in range(N):
            data_input = self.listWidget.item(i).text()
            if data_input != '':
                self.data_input_list.append(data_input)
                
    def make_to_read_lists(self):
        self.measurements_to_read = []  # Measurements class
        self.settings_to_read = []  # lq_paths strings
        for data_input in self.data_input_list:
            if data_input.startswith('measurements'):
                _, name, _ = data_input.split('.')
                if not name in self.measurements_to_read:
                    self.measurements_to_read.append(self.app.measurements[name])
            else:  # is a setting path
                self.settings_to_read.append(data_input)    

    def new_plot_line(self, dset_name):
        self.plot_x_comboBox.addItem(dset_name)
        self.plot_lines.update({dset_name:self.plot.plot([1, 3, 2, 4])})
        self.plot_x_data_name = dset_name
        N = self.plot_x_comboBox.count()
        self.plot_x_comboBox.setCurrentIndex(N - 1)
                
    def dset_name(self, prefix, suffix):
        '''data_set name generator'''
        return '_'.join((prefix, suffix))
        
    def add_to_data_sets(self, dset_name, values):
        if self.valid_type(values):
            if not dset_name in self.data_sets.keys():
                self.data_sets.update({dset_name:{'plot_values':[np.array(values).sum()],  # needed such
                                       'values':[np.array(values)]}})
                self.new_plot_line(dset_name)
            else:
                self.data_sets[dset_name]['plot_values'].append(np.array(values).sum())
                if self.settings['compress']:
                    if np.array(values) == self.data_sets[dset_name]['values'][-1]:
                        return    
                self.data_sets[dset_name]['values'].append(np.array(values))
                
    def add_attr_value_to_data_sets(self, obj, attr):
        values = getattr(obj, attr)
        if type(values) == dict:
            for attr, _values in values.items():
                dset_name = self.dset_name(obj.name, attr)
                self.add_to_data_sets(dset_name, _values)  
        else:
            dset_name = self.dset_name(obj.name, attr)
            self.add_to_data_sets(dset_name, values)  
                
    def add_setting_value_to_data_sets(self, path):
        value = self.app.lq_path(path).read_from_hardware()
        _, name, setting = path.split('/')       
        dset_name = self.dset_name(name, setting)
        self.add_to_data_sets(dset_name, value)

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
            if type(x) in (np.array, dict, np.ndarray, set):
                return type(x)
            if not hasattr(x, '__iter__'):
                return type(x)        
            elif len(x) == 0:
                return None
            else:
                return get_type(x[0])  # if attribute is list of lists
            
        return get_type(x) in (int, float, np.array, bool, np.ndarray, dict, set)
        
    def pre_run(self): 
        self.display_ready = False
        self.plot.clear()
        self.ii = 0
        self.data_sets = {}
        self.plot_lines = {}
        self.plot_x_comboBox.clear()
                
        if self.settings['sweep_setting'] in ('', '0'):
            self.plot.setTitle('set a quantity to sweep', color='r')
            self.interrupt_measurement_called = True
            return

        self.make_data_input_list()        
        if not len(self.data_input_list):
            self.plot.setTitle('add a data attribute', color='r')
            self.interrupt_measurement_called = True
            return
        
        self.make_to_read_lists()

        self.plot.setTitle('measurement started', color='g')
        
    def run(self):
        S = self.settings
        N = len(self.range.sweep_array)
        for ii, x in enumerate(self.range.sweep_array):
            if self.interrupt_measurement_called:
                break
            self.set_progress(100.0 * (ii + 1) / N)
            self.app.lq_path(S['sweep_setting']).update_value(x)
            time.sleep(S['collection_delay'])

            # perform all measurements
            for measurement in self.measurements_to_read:
                if self.interrupt_measurement_called:
                    break                
                self.run_prepare_sequence(measurement.name)
                self.start_nested_measure_and_wait(measurement, nested_interrupt=False)
                # get measurement attributes
                for data_input in self.data_input_list:
                    if data_input.startswith('measurements'):
                        _, name, attr = data_input.split('.')
                        if name == measurement.name:
                            self.add_attr_value_to_data_sets(measurement, attr)

            # read settings                            
            for path in self.settings_to_read:
                self.add_setting_value_to_data_sets(path)
            
            self.display_ready = True
            self.ii = ii
            
        self.save_h5_data()
        
    def save_h5_data(self):
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_meas_group = h5_io.h5_create_measurement_group(self, self.h5_file)
        for k, v in self.data_sets.items():
            self.h5_meas_group[str(k) + '_plot_values'] = v['plot_values']
            self.h5_meas_group[str(k)] = np.squeeze(v['values'])
        self.h5_meas_group['sweep_array'] = self.range.sweep_array
        self.h5_meas_group.attrs['sweep_quantity'] = self.settings['sweep_setting']
        self.h5_file.close()

    def post_run(self):
        self.plot.setTitle('finished', color='g')       
        self.plot.addItem(self.set_sweep_setting)     

    def update_display(self):
        if self.display_ready:
            ii = self.ii + 1
            x = self.data_sets[self.plot_x_data_name]['plot_values'][:ii]
            for k in self.data_sets:
                if k != self.plot_x_data_name:
                    y = norm(self.data_sets[k]['plot_values'][:ii])
                    if self.settings['polar_plot']:
                        x, y = y * np.cos(x), y * np.sin(x)
                    self.plot_lines[k].setData(x, y)
                else:
                    self.plot_lines[k].clear()
    
