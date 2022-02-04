'''
Created on Jul 8, 2021

@author: Benedikt Ursprung
'''

from ScopeFoundry import BaseMicroscopeApp


class PMDTestApp(BaseMicroscopeApp):

    name = 'pmd_test_app'
    
    def setup(self):
        
        from ScopeFoundryHW.laser_quantum.pmd24HW import PMD24HW
        self.add_hardware(PMD24HW(self))        
        
        from ScopeFoundryHW.laser_quantum.laser_quantum_optimizer import LaserQuantumOptimizer
        self.add_measurement(LaserQuantumOptimizer)


if __name__ == '__main__':
    import sys
    app = PMDTestApp(sys.argv)
    sys.exit(app.exec_())
