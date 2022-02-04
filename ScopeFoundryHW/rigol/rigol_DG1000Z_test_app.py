'''
Created on Apr 26, 2021

@author: lab
'''
from ScopeFoundry.base_app import BaseMicroscopeApp


class RigolDG1000ZTestApp(BaseMicroscopeApp):
    
    def setup(self):
        from ScopeFoundryHW.rigol.rigol_DG1000Z_hw import RigolDG1000ZHW
        hw = self.add_hardware(RigolDG1000ZHW(self))
        
        
if __name__ == '__main__':

    app = RigolDG1000ZTestApp([])
    app.exec_()