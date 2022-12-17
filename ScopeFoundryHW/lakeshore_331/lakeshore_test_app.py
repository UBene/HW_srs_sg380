'''
Created on Apr 26, 2021

@author: lab
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.lakeshore_331.lakeshore_hw import Lakeshore331HW
from ScopeFoundryHW.lakeshore_331.lakeshore_measure import LakeshoreMeasure


class LakeshoreTestApp(BaseMicroscopeApp):
    
    def setup(self):
        hw = self.add_hardware(Lakeshore331HW)
        self.add_measurement(LakeshoreMeasure)
        
        hw.settings['port'] = 'COM21'
        
if __name__ == '__main__':

    app = LakeshoreTestApp([])
    #app.qtapp.setStyle('Fusion')
    app.exec_()