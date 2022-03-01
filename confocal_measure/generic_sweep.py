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
                          description='guesses data set duplicates across iteration and only stores one copy.')
        self.setup_prepare_sequences_settings()
        self.setup_target_measurements()
        
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
            
    def setup_target_measurements(self):
        '''checks if measurements of the app has a "data" (dictionary) 
            attribute and if so it adds a measurement. 
            Note that GenericSweeper should be the last added to make this work properly'''
        self.includes_measurements = []
        for m in self.app.measurements.values():
            if hasattr(m, 'data'):
                self.settings.New(m.name, bool, initial=False,
                        description='measurement is run and its .data dict at each iteration will be collected.')
                self.includes_measurements.append(m.name)
            
    def setup_figure(self):
        self.ui = QWidget()

        # # Generate settings Layout
        # layout (V)
        # - settings_layout (H)
        #     sweep_settings_groubBox | target_measurements_groubBox |             target_data_groupBox
        #                                                                      target_data_layout (H)
        #                                                              target_data_layout_L (V) | target_data_layout_R (V)
        # - graph_layout
        # - post_process_layout (H)
        layout = QVBoxLayout(self.ui)
        settings_layout = QHBoxLayout()
        layout.addLayout(settings_layout)
        sweep_settings_groubBox = QGroupBox('sweep settings')
        sweep_settings_layout = QVBoxLayout(sweep_settings_groubBox)
        target_measurements_groubBox = QGroupBox('target measurements')
        target_measurements_layout = QVBoxLayout(target_measurements_groubBox)
        target_measurements_groubBox.setToolTip('''measurements with a <i>data</i> dictionary will show up here. 
                                    If checked the measurement is run and its data is 
                                    collected at every iteration and saved''')
        target_data_groupBox = QGroupBox('additional attributes && settings targets')
        target_data_groupBox.setToolTip('''runs corresponding measurement and save
                                            the attribute or reads current setting value''')
        target_data_layout = QHBoxLayout(target_data_groupBox)
        target_data_groupBox.setMaximumHeight(300)
            
        for w in [sweep_settings_groubBox,
                   target_measurements_groubBox,
                   target_data_groupBox]: 
            settings_layout.addWidget(w)

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

        # target_measurements_layout
        w = self.settings.New_UI(self.includes_measurements)
        target_measurements_layout.addWidget(w)

        # start_stop
        target_measurements_layout.addWidget(self.settings.activation.new_pushButton())
        
        # target_data_layout
        target_data_layout_L = QVBoxLayout()
        target_data_layout_R = QVBoxLayout()
        for l in [target_data_layout_L, target_data_layout_R]:
            target_data_layout.addLayout(l)      

        # target_data_layout_L
        attrs = self.get_list_of_attributes()
        self.target_data_lineEdit = QLineEdit()
        completer = QCompleter(attrs + paths)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setModelSorting(QCompleter.UnsortedModel)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.target_data_lineEdit.setCompleter(completer)
        target_data_layout_L.addWidget(self.target_data_lineEdit)
        
        add_btn = QPushButton('add -->')
        target_data_layout_L.addWidget(add_btn)
        add_btn.clicked.connect(self.on_add_target_data_attr_item)
        
        remove_btn = QPushButton('remove')
        target_data_layout_L.addWidget(remove_btn)
        remove_btn.clicked.connect(self.on_remove_target_data_attr_item)   

        # target_data_layout_R 
        self.target_data_listWidget = QListWidget()
        self.target_data_listWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.target_data_listWidget.setDragDropMode(QListWidget.DragDrop)
        target_data_layout_R.addWidget(self.target_data_listWidget)
        self.target_data_listWidget.keyReleaseEvent = self._keyReleaseEvent

        # graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph_layout)
        self.plot = self.graph_layout.addPlot()
        self.status = {'title':"generic sweep", 'color':'g'}       
        self.plot.showGrid(True, True)
        self.display_ready = False
        self.set_sweep_setting = self.plot.addLine(x=0, movable=True, pen='y')

        # post_process_layout
        post_process_layout = QHBoxLayout()
        post_process_layout.addWidget(QLabel('plot x'))
        self.plot_x_comboBox = QComboBox()
        post_process_layout.addWidget(self.plot_x_comboBox)
        layout.addLayout(post_process_layout)
        self.plot_x_comboBox.currentTextChanged.connect(self.on_plot_x_changed)
        post_process_layout.addWidget(self.settings.polar_plot.new_default_widget())
        set_btn = QPushButton('set sweep setting')
        set_btn.setToolTip('set <b>sweep_quantity</b> to equivalent value of yellow line.')
        post_process_layout.addWidget(set_btn)
        set_btn.clicked.connect(self.on_set_sweep_setting)
        
    def _keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.on_remove_target_data_attr_item()
        
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
                
    def on_add_target_data_attr_item(self):
        target_data = self.target_data_lineEdit.text()
        self.target_data_listWidget.addItem(QListWidgetItem(target_data))
        
    def on_remove_target_data_attr_item(self): 
        item = self.target_data_listWidget.item(self.target_data_listWidget.currentRow())            
        self.target_data_listWidget.takeItem(self.target_data_listWidget.row(item))
        del item
        
    def make_target_data_list(self): 
        self.target_data_list = []  
        for name in self.includes_measurements:
            if self.settings[name]:
                target_data = f'measurements.{name}.data'
                self.target_data_list.append(target_data)
        self.target_data_list.append(self.settings['sweep_setting'])
        N = self.target_data_listWidget.count()        
        for i in range(N):
            target_data = self.target_data_listWidget.item(i).text()
            if target_data != '':
                self.target_data_list.append(target_data)
                
    def make_target_lists(self):
        self.target_measurements = []  # Measurement class
        self.target_settings = []  # lq_paths strings
        for target_data in self.target_data_list:
            if target_data.startswith('measurements'):
                _, name, _ = target_data.split('.')
                if not name in self.target_measurements:
                    self.target_measurements.append(self.app.measurements[name])
            else:  # is a setting path
                self.target_settings.append(target_data)    

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
            if m.name != self.name:
                for a in dir(m):
                    if not callable(getattr(m, a)) and\
                        a.startswith('__') == False and\
                        self.valid_type(x=getattr(m, a)) and\
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
            elif type(x) in (list, set) and len(x) > 0:
                return get_type(x[0])
                
        return get_type(x) in (int, float, np.array, bool, np.ndarray, dict, set, None)
        
    def pre_run(self): 

        self.display_ready = False
        self.plot.clear()
        self.ii = 0
        self.data_sets = {}
        self.plot_lines = {}

        self.plot_x_comboBox.clear()
                
        if self.settings['sweep_setting'] in ('', '0'):
            self.status = {'title':'set a quantity to sweep', "color":'r'}
            return

        self.make_target_data_list()        
        if not len(self.target_data_list):
            self.status = {'title':'add a data attribute', "color":'r'}
            return
        
        self.make_target_lists()
        self.status = {'title':'measurement started', 'color':'g'}       
        
    def run(self):
        S = self.settings
        N = len(self.range.sweep_array)
        for ii, x in enumerate(self.range.sweep_array):
            if self.interrupt_measurement_called:
                break            
            self.set_progress(100.0 * (ii + 1) / N)
            self.app.lq_path(S['sweep_setting']).update_value(x)
            time.sleep(S['collection_delay'])

            # perform target measurements
            for measurement in self.target_measurements:
                if self.interrupt_measurement_called:
                    break                
                self.run_prepare_sequence(measurement.name)
                self.start_nested_measure_and_wait(measurement, nested_interrupt=False)
                self.status = {'title':f'{measurement.name} ({ii+1} of {N})', "color":'g'}
                # get measurement attributes
                for target_data in self.target_data_list:
                    if target_data.startswith('measurements'):
                        _, name, attr = target_data.split('.')
                        if name == measurement.name:
                            self.add_attr_value_to_data_sets(measurement, attr)

            # target settings                            
            for path in self.target_settings:
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
        self.plot.addItem(self.set_sweep_setting)     

    def update_display(self):
        self.plot.setTitle(**self.status)
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
    
