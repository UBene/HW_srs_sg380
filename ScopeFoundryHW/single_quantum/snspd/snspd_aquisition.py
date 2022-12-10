'''
Created on Dec 9, 2022

@author: Benedikt Ursprung
'''
from ScopeFoundry import Measurement
from ScopeFoundry import h5_io


class SNSPDAquireCounts(Measurement):

    name = "snspd_aquire_counts"

    def setup(self):
        self.settings.New("N", int, initial=10,
                          description="number of aquisitions")
        self.data = {'timestamps': [0], 'counts': [0]}

    def run(self):
        t, counts = self.app.hardware['snspd'].acquire_cnts(self.settings['N'])
        self.data['timestamps'] = t
        self.data['counts'] = counts

        print(self.data)

    def save_h5_data(self):
        h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        h5_meas_group = h5_io.h5_create_measurement_group(self, h5_file)
        for k, v in self.data.items():
            h5_meas_group[k] = v
        h5_file.close()
