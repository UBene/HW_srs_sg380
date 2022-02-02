from ScopeFoundry.base_app import BaseMicroscopeApp
import logging

logging.basicConfig(level=logging.DEBUG)

class CrystalTechAOTF_App(BaseMicroscopeApp):
    
    name = 'CrystalTechAOTF_App'
    
    def setup(self):
        

        from ScopeFoundryHW.crystaltech_aotf.crystaltech_aotf_hc import CrystalTechAOTF
        
        self.add_hardware(CrystalTechAOTF(self))
        
    
if __name__ == '__main__':
    import sys
    app = CrystalTechAOTF_App(sys.argv)
    sys.exit(app.exec_())