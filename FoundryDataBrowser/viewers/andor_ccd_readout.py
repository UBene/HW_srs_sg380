from ScopeFoundry.data_browser import DataBrowserView
from FoundryDataBrowser.viewers.plot_n_fit import PlotNFit, PeakUtilsFitter
import numpy as np
import h5py


class AndorCCDReadout(DataBrowserView):

    name = 'andor_ccd_readout'

    def setup(self):

        self.plot_n_fit = PlotNFit(fitters=[PeakUtilsFitter()])
        self.ui = self.plot_n_fit.ui
        self.plot_n_fit.settings['fit_options'] = 'DisableFit'

    def is_file_supported(self, fname):
        return "andor_ccd_readout.npz" in fname or "andor_ccd_readout.h5" in fname

    def on_change_data_filename(self, fname):
        if fname is None:
            fname = self.databrowser.settings['data_filename']

        try:
            if '.npz' in fname:
                dat = self.dat = np.load(fname)
                spec = dat['spectrum'].sum(axis=0)
                wls = np.array(dat['wls'])
            elif '.h5' in fname:
                with h5py.File(fname, 'r') as H:
                    M = H['measurement/andor_ccd_readout']
                    spec = np.array(M['spectrum'][:]).sum(axis=0)
                    wls = M['wls'][:]

            self.plot_n_fit.set_data(wls, spec)

        except Exception as err:
            self.plot_n_fit.set_data([0, 1, 2, 3], [1, 3, 2, 4])
            self.databrowser.ui.statusbar.showMessage(
                "failed to load %s:\n%s" % (fname, err))
            raise(err)
