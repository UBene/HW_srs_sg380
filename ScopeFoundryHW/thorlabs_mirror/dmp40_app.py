'''
Created on Aug 22, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''


from ScopeFoundry import BaseMicroscopeApp

class DMP40_app(BaseMicroscopeApp):
    
    def setup(self):
        from ScopeFoundryHW.thorlabs_mirror.dmp40_hw import ThorlabsDMP40_HW
        self.add_hardware(ThorlabsDMP40_HW(self))
        
        from ScopeFoundryHW.thorlabs_mirror.dmp40_measure import ThorlabsDMP40_Measure
        self.add_measurement(ThorlabsDMP40_Measure(self))
        
        self.ui.show()
        self.ui.activateWindow()
    
if __name__ == '__main__':
    from sys import argv, exit
    app = DMP40_app(argv)
    exit(app.exec_())
    
    