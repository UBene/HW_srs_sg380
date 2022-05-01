from ScopeFoundry.data_browser import DataBrowserView
from FoundryDataBrowser.viewers.plot_n_fit import PlotNFit, PeakUtilsFitter
import h5py


class PicamReadout(DataBrowserView):

    name = "picam_readout"

    def setup(self):

        self.plot_n_fit = PlotNFit(fitters=[PeakUtilsFitter()])
        self.ui = self.plot_n_fit.get_docks_as_dockarea()
        self.plot_n_fit.settings["fit_options"] = "DisableFit"

    def is_file_supported(self, fname):
        return "picam_readout" in fname

    def on_change_data_filename(self, fname):

        with h5py.File(fname, 'r') as H:
            M = H['measurement/andor_ccd_readout']
            spec = M['spectrum'][:]
            wls = M['wls'][:]

        self.plot_n_fit.set_data(wls, spec, is_data_to_fit=True)
