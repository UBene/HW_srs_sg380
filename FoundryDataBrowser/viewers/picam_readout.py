from ScopeFoundry.data_browser import DataBrowserView
from FoundryDataBrowser.viewers.plot_n_fit import PlotNFit, PeakUtilsFitter
import numpy as np
import h5py

class PicamReadout(DataBrowserView):
    
    name = 'picam_readout'
    
    def setup(self):
        
        self.plot_n_fit = PlotNFit(fitters=[PeakUtilsFitter()])                
        self.ui = self.plot_n_fit.get_docks_as_dockarea()
        self.plot_n_fit.settings['fit_options'] = 'DisableFit'

        
    def is_file_supported(self, fname):
        return 'picam_readout' in fname

    def on_change_data_filename(self, fname):

        dat = self.dat = h5py.File(fname)
        self.M = dat['measurement/picam_readout']
        self.spec = np.array(self.M['spectrum']).sum(axis=0)
        self.wls = np.array(self.M['wavelength'])
            
        self.plot_n_fit.update_data(self.wls, self.spec)
            
