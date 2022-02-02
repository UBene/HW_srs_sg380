from .asi_hyperspec_scan import ASIHyperSpec2DScan


class AndorAsiHyperSpec2DScan(ASIHyperSpec2DScan):
    
    name = "andor_asi_hyperspec_scan"
    
    def scan_specific_setup(self):
        self.spec = self.app.measurements['andor_ccd_readout']
        ASIHyperSpec2DScan.scan_specific_setup(self)

    def pre_scan_setup(self):
        self.spec.settings['acquire_bg'] = False
        ASIHyperSpec2DScan.pre_scan_setup(self)