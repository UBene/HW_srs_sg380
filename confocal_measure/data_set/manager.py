'''
Created on Mar 6, 2022

@author: Benedikt Ursprung
'''
import numpy as np

from qtpy import QtCore


class DataSetManager(QtCore.QObject):
    
    new_data_set_registered = QtCore.Signal(str)
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.reset()
        self.set_compress(False)
            
    def set_compress(self, compress:bool):
        self.compress = compress
                
    def reset(self):
        self.data_sets = {}
        
    def dset_name(self, prefix, suffix):
        '''data_set name generator'''
        return '_'.join((prefix, suffix))
    
    def add(self, dset_name, values):

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
                
    def add_attr_value(self, obj, attr):
        values = getattr(obj, attr)
        if type(values) == dict:
            for attr, _values in values.items():
                dset_name = self.dset_name(obj.name, attr)
                self.add(dset_name, _values)  
        else:
            dset_name = self.dset_name(obj.name, attr)
            self.add(dset_name, values)  
                
    def add_setting_value(self, lq_path:str):
        value = self.app.lq_path(lq_path).read_from_hardware()
        _, name, setting = lq_path.split('/')       
        dset_name = self.dset_name(name, setting)
        self.add(dset_name, value)
                
    def add_to_meas_group(self, h5_meas_group):
        for k, v in self.data_sets.items():
            h5_meas_group[str(k) + '_plot_values'] = v['plot_values']
            h5_meas_group[str(k)] = np.squeeze(v['values'])
            
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
        
