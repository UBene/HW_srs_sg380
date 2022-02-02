from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundryHW.alicat_eip.alicat_eip_mfc_hw import Alicat_EIP_MFC_HW
from ScopeFoundryHW.alicat_eip.alicat_eip_pc_hw import Alicat_EIP_PC_HW

class AlicatTestApp(BaseMicroscopeApp):
    name = 'alicat_test_app'
    
    def setup(self):
        self.add_hardware(Alicat_EIP_MFC_HW(self))
        self.add_hardware(Alicat_EIP_PC_HW(self))
        
        


if __name__ == '__main__':
    
    app = AlicatTestApp()
    
    app.exec_()