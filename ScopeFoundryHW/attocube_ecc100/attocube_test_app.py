from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PyQt5').setLevel(logging.WARN)
logging.getLogger('ipykernel').setLevel(logging.WARN)
logging.getLogger('traitlets').setLevel(logging.WARN)
logging.getLogger('LoggedQuantity').setLevel(logging.WARN)

class AttocubeTestApp(BaseMicroscopeApp):
    
    name="attocube_test_app"
    
    def setup(self):
        from ScopeFoundryHW.attocube_ecc100 import AttoCubeXYZStageHW
        self.add_hardware(AttoCubeXYZStageHW(self, ax_names='xyz'))
        self.add_hardware(AttoCubeXYZStageHW(self, name='attocube_dev2', ax_names=['r', 'theta', 'phi']))
        
        #from ScopeFoundryHW.attocube_anc150.anc150_optimizer import ANC_Optimizer
        #self.add_measurement(ANC_Optimizer(self))
        
        #from ScopeFoundryHW.attocube_anc150.anc_explore_measure import ANC_RemoteMeasure
        #self.add_measurement(ANC_RemoteMeasure(self))
        from ScopeFoundryHW.attocube_ecc100.attocube_stage_control import AttoCubeStageControlMeasure
        self.add_measurement(AttoCubeStageControlMeasure(self, name='attocube_dev1'))
        self.add_measurement(AttoCubeStageControlMeasure(self, name='attocube_dev2', hw_name='attocube_dev2'))
        
        from ScopeFoundryHW.attocube_ecc100.attocube_slowscan import AttoCube2DSlowScan
        self.add_measurement(AttoCube2DSlowScan(self))
        
        #self.ui.lq_trees_groupBox.hide()
        
if __name__ == '__main__':
    import sys
    app = AttocubeTestApp(sys.argv)
    sys.exit(app.exec_())    
        