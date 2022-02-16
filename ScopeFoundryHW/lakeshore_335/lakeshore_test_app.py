'''
Created on Jan 15, 2022

@author: Benedikt Ursprung

requires: pip install lakeshore
'''
from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.lakeshore_335.lakeshore_hw import Lakeshore335HW
from ScopeFoundryHW.lakeshore_335.lakeshore_measure import LakeshoreMeasure

class LakeshoreTestApp(BaseMicroscopeApp):
    
    def setup(self):
        hw = self.add_hardware(Lakeshore335HW(self))
        self.add_measurement(LakeshoreMeasure(self))
        
        
if __name__ == '__main__':

    app = LakeshoreTestApp([])
    #app.qtapp.setStyle('Fusion')
    app.exec_()