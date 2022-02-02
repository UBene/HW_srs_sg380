import numpy as np
from .asi_hyperspec_scan import ASIHyperSpec2DScan, ASIHyperSpec3DScan

class OceanOpticsAsiHyperSpec2DScan(ASIHyperSpec2DScan):
    
    name = "oo_asi_hyperspec_scan"
    
    def scan_specific_setup(self):
        self.spec = self.app.measurements['oo_spec_live']
        ASIHyperSpec2DScan.scan_specific_setup(self) 
        
    def setup_figure(self):
        ASIHyperSpec2DScan.setup_figure(self)
        self.spec.roi.sigRegionChanged.connect(self.recompute_image_map)        
                
    def collect_pixel(self, pixel_num, k, j, i):
        ASIHyperSpec2DScan.collect_pixel(self, pixel_num, k, j, i)
        ind_min = np.searchsorted(self.wls,self.spec.settings.roi_min.val)
        ind_max = np.searchsorted(self.wls,self.spec.settings.roi_max.val)
        self.display_image_map[k,j,i] = self.spec_map[k,j,i,ind_min:ind_max].sum()
        if self.spec.settings['baseline_subtract']:
            self.display_image_map[k,j,i] -= self.spec.settings.baseline_val.val*(ind_max-ind_min)
        if pixel_num == 0 and self.settings['save_h5']:
            self.h5_meas_group.create_dataset('dark_indices', data=self.spec.hw.get_dark_indices())
            
    
    def recompute_image_map(self):
        if not hasattr(self, 'display_image_map'):
            self.display_image_map = np.zeros(self.scan_shape)
            
        ind_min = np.searchsorted(self.wls,self.spec.settings.roi_min.val)
        ind_max = np.searchsorted(self.wls,self.spec.settings.roi_max.val)
        if self.settings['debug']: print("Min %d Max %d" % (ind_min,ind_max))
        self.display_image_map = np.sum(self.spec_map[:,:,:,ind_min:ind_max],axis=-1)
        if self.spec.settings['baseline_subtract']:
            non_zero_index = np.nonzero(self.display_image_map)
            self.display_image_map[non_zero_index] -= self.spec.settings.baseline_val.val*(ind_max-ind_min)
    
class OceanOpticsAsiHyperSpec3DScan(ASIHyperSpec3DScan):
    
    name = "oo_asi_hyperspec_3d_scan"
    
    def scan_specific_setup(self):
        self.spec = self.app.measurements['oo_spec_live']
        ASIHyperSpec3DScan.scan_specific_setup(self) 
        
    def setup_figure(self):
        ASIHyperSpec3DScan.setup_figure(self)
        self.spec.roi.sigRegionChanged.connect(self.recompute_image_map)        
                
    def collect_pixel(self, pixel_num, k, j, i):
        ASIHyperSpec3DScan.collect_pixel(self, pixel_num, k, j, i)
        ind_min = np.searchsorted(self.wls,self.spec.settings.roi_min.val)
        ind_max = np.searchsorted(self.wls,self.spec.settings.roi_max.val)
        
        self.display_image_map[k,j,i] = self.spec_map[k,j,i,ind_min:ind_max].sum()
        if self.spec.settings['baseline_subtract']:
            self.display_image_map[k,j,i] -= self.spec.settings.baseline_val.val*(ind_max-ind_min)
        if pixel_num == 0 and self.settings['save_h5']:
            self.h5_meas_group.create_dataset('dark_indices', data=self.spec.hw.get_dark_indices())
    
    def recompute_image_map(self):
        if not hasattr(self, 'display_image_map'):
            self.display_image_map = np.zeros(self.scan_shape)
            
        ind_min = np.searchsorted(self.spec.wls,self.spec.settings.roi_min.val)
        ind_max = np.searchsorted(self.spec.wls,self.spec.settings.roi_max.val)
        if self.settings['debug']: print("Min %d Max %d" % (ind_min,ind_max))
        self.display_image_map = np.sum(self.spec_map_h5[:,:,:,ind_min:ind_max],axis=-1)
        if self.spec.settings['baseline_subtract']:
            non_zero_index = np.nonzero(self.display_image_map)
            self.display_image_map[non_zero_index] -= self.spec.settings.baseline_val.val*(ind_max-ind_min)
    