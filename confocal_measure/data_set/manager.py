'''
Created on Mar 6, 2022

@author: Benedikt Ursprung
'''
import numpy as np

from qtpy import QtCore
from ScopeFoundry.measurement import Measurement
from ScopeFoundry.hardware import HardwareComponent
from typing import Union, Sequence


class DataSetManager(QtCore.QObject):
    
    """
    A class to represent a data sets.

    data_set = {'dataset_name_1':{'values':[[data0], [data1] ...],
                                  'plot_values':[sum([data0]), sum([data1])...]}
         ....
         }
        


    dataset_name is autoenerated if the two convience methods `add_from_obj_attr`
    and `add_from_setting`
    
    ...


    Setter Methods
    -------
    reset()
        deletes all entries
        
    add_from_obj_attr(obj:Union[Measurement, HardwareComponent], attr:str)
    add_from_setting(lq_path:str):
    
        
    Getter Methods
    -------
    get_plot_values(dset_name):
    get_values(dset_name):
    save_to_h5_meas_group(h5_meas_group)
    """
    
    new_data_set_registered = QtCore.Signal(str)
    
    def __init__(self, measurement:Measurement):
        super().__init__()
        self.measurement = measurement
        self.app = measurement.app
        self.reset()
        self.set_compress(False)
        measurement.settings.New('compress_data', bool, initial=False,
                          description='guesses data set duplicates across iteration and only stores one copy.')
        measurement.compress_data.add_listener(self.data_sets.set_compress)
            
    def set_compress(self, compress:bool):
        self.compress = compress
                
    def reset(self):
        self.data_sets = {}
        
    def dset_name(self, names:Sequence):
        '''data_set name generator'''
        return '_'.join(names)
    
    def _add(self, dset_name:str, values):

        if self.valid_type(values):
            if not dset_name in self.data_sets.keys():
                self.data_sets.update({dset_name:{'plot_values':[np.array(values).sum()],  # needed such
                                       'values':[np.array(values)]}})
                self.new_data_set_registered.emit(dset_name)
            else:
                self.data_sets[dset_name]['plot_values'].append(np.array(values).sum())
                if self.compress:
                    if np.array(values) == self.data_sets[dset_name]['values'][-1]:
                        return    
                self.data_sets[dset_name]['values'].append(np.array(values))
                
    def add_from_obj_attr(self, obj:Union[Measurement, HardwareComponent],
                       attr:str):
        values = getattr(obj, attr)
        if type(values) == dict:
            for attr, _values in values.items():
                dset_name = self.dset_name((obj.name, attr))
                self._add(dset_name, _values)  
        else:
            dset_name = self.dset_name((obj.name, attr))
            self._add(dset_name, values)  
                
    def add_from_setting(self, lq_path:str):
        value = self.app.lq_path(lq_path).read_from_hardware()
        _, name, setting = lq_path.split('/')       
        dset_name = self.dset_name((name, setting))
        self._add(dset_name, value)
                
    def save_to_h5_meas_group(self, h5_meas_group):
        for k, v in self.data_sets.items():
            h5_meas_group[str(k) + '_plot_values'] = v['plot_values']
            h5_meas_group[str(k)] = np.squeeze(v['values'])
            
    def get_plot_values(self, dset_name):
        return self.data_sets[dset_name]['plot_values']
    
    def get_values(self, dset_name):
        return self.data_sets[dset_name]['values']
    
    def __contains__(self, key):
        return key in self.data_sets
    
    def __getitem__(self, key):
        return self.data_sets[key] 

    def __setitem__(self, key, value):
        self.data_sets[key] = value
    
    def keys(self):
        return self.data_sets.keys()
    
    def items(self):
        return self.data_sets.items()
            
    def valid_type(self, x):

        def get_type(x):
            if type(x) in (np.array, dict, np.ndarray, set):
                return type(x)
            # elif not hasattr(x, '__iter__'):
            #    return type(x)        
            # elif len(x) == 0:
            #    return None
            # elif type(x) in (list, set) and len(x) > 0:
            #    return get_type(x[0])
                
        return get_type(x) in (int, float, np.array, bool, np.ndarray, dict, set, None)
    
    def get_list_of_attributes(self):
        attrs = []        
        for m in self.app.measurements.values():
            if m.name != self.measurement.name:
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
        
