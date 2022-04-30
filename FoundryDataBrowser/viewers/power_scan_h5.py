import numpy as np
import h5py
from qtpy import QtWidgets
import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea

from ScopeFoundry.widgets import DataSelector
from ScopeFoundry.data_browser import DataBrowserView
from FoundryDataBrowser.viewers.plot_n_fit import (
    PlotNFit,
    NonLinearityFitter,
)
import glob
import json
import os


class PowerScanUI(dockarea.DockArea):

    def __init__(
        self, plot_n_fit,
    ):
        super().__init__()

        self.plot_n_fit = plot_n_fit
        self.plot_n_fit.ui.plot.setLogMode(True, True)

        self.data_select_widget = QtWidgets.QWidget()
        self.data_select_layout = QtWidgets.QHBoxLayout(
            self.data_select_widget)
        self.data_select_dock = self.addDock(
            name="data select", widget=self.data_select_widget,
        )
        self.data_select_dock.setStretch(2, 1)

        self.fit_graph_dock = self.addDock(
            plot_n_fit.ui.graph_dock,
            position="bottom",
            relativeTo=self.data_select_dock,
        )

        self.graph_layout = pg.GraphicsLayoutWidget()
        self.spec_plot = self.graph_layout.addPlot()
        self.spec_dock = self.addDock(
            None,
            name="spectrum",
            position="right",
            relativeTo=self.fit_graph_dock,
            widget=self.graph_layout,
        )
        self.spec_line = self.spec_plot.plot(
            [1, 2, 3, 4], [1, 3, 2, 4], pen="r")

        plot_n_fit.ui.settings_dock.setStretch(1, 2)
        self.fit_settings_dock = self.addDock(
            plot_n_fit.ui.settings_dock, "right", self.spec_dock
        )

        # self.target = pg.TargetItem(pen="r")
        # self.target = pg.ScatterPlotItem(pen="r", symbol='o', size=12)
        # self.plot_n_fit.ui.plot.addItem(self.target)
        self.target = self.plot_n_fit.ui.plot.plot(pen="r", symbol='o')
        self.target_label = pg.TextItem(color="r")
        self.plot_n_fit.ui.plot.addItem(self.target_label)

    def add_to_select_layout(self, widget):
        self.data_select_layout.addWidget(widget)

    def view_position(self, x, y):
        if self.plot_n_fit.ui.plot.ctrl.logXCheck.isChecked():
            x = np.log10(x)
        if self.plot_n_fit.ui.plot.ctrl.logYCheck.isChecked():
            y = np.log10(y)
        return (x, y)

    def set_target(self, x, y, text=""):
        self.target.setData(x=[x], y=[y])
        x, y = self.view_position(x, y)
        # self.target.setPos(x, y)
        self.target_label.setPos(x, y)
        self.target_label.setText(text)


class PowerScanH5View(DataBrowserView):

    name = "power_scan_h5"

    def is_file_supported(self, fname):
        return ("power_scan" in fname) and (".h5" in fname)

    @property
    def dir_fname(self):
        return os.path.dirname(self.fname)

    @property
    def json_file(self):
        return os.path.dirname(self.fname) + '/power_scans_configs.json'

    @property
    def notebook_file_target(self):
        return os.path.dirname(self.fname) + '/power_scans_h5_configured_plot.ipynb'

    @property
    def notebook_file_original(self):
        return fr'{os.getcwd()}\viewers\power_scans_h5_configured_plot.ipynb'

    @property
    def base_fname(self):
        return os.path.basename(self.fname)

    def load_params_from_json(self):
        if not len(glob.glob(self.json_file)):
            print('no file file found')
            return {}
        with open(self.json_file, 'r') as f:
            return json.load(f)

    def commit_params(self):
        params_collection = self.load_params_from_json()
        params_collection[self.base_fname] = self.get_params_dict()
        with open(self.json_file, 'w') as outfile:
            json.dump(params_collection, outfile, indent=4)

    def get_params_dict(self) -> {}:
        params = {k: lq.value for k,
                  lq in self.settings.as_dict().items()}
        params['bg_selector'] = self.bg_selector.get_params_dict()
        params['signal_selector'] = self.signal_selector.get_params_dict()
        params['plot_n_fit'] = self.plot_n_fit.get_params_dict()
        return params

    def update_params_from_json(self):
        params_collection = self.load_params_from_json()
        if self.base_fname in params_collection:
            self.set_params_dict(params_collection[self.base_fname])
            self.update_fit()
        else:
            print('no entry')

    def set_params_dict(self, params: {}):
        self.bg_selector.set_params_dict(params['bg_selector'])
        self.signal_selector.set_params_dict(params['signal_selector'])
        self.plot_n_fit.set_params_dict(params['plot_n_fit'])
        # self.plot_n_fit.data_selector.set_params_dict(params['data_selector'])
        for name, lq in self.settings.as_dict().items():
            lq.update_value(params.get(name, lq.value))

    def setup(self):

        # data format
        self.wls = np.arange(512)
        self.spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512)) + 1
        self.power_arrays = {
            "pm_powers": np.arange(21) / 2.1,
            "pm_powers_after": np.arange(21) / 2,
            "power_wheel_position": np.arange(21),
        }

        # settings
        self.settings.New("spec_index", dtype=int, initial=0)
        self.settings.New("power_binning", dtype=int, initial=1)
        self.power_x_axis_choices = list(self.power_arrays.keys())
        self.settings.New(
            "power_x_axis",
            dtype=str,
            initial="pm_powers",
            choices=self.power_x_axis_choices,
        )
        self.settings.New("channel", int, initial=0, vmin=0)
        self.settings.New("conversion_factor", float, initial=1.0)
        self.settings.New("ignore", bool, initial=False,
                          description='for subsequent analysis only: a flag in power_scans_configs.json file')
        self.settings.New('info', str, initial='',
                          description='for subsequent analysis only: additional information string')

        # data selectors
        self.signal_selector = DataSelector(name="signal select")
        self.bg_selector = DataSelector(name="background select")

        # listeners
        self.settings.spec_index.add_listener(self.update_spec_plot)
        # self.settings.power_x_axis.add_listener(self.update_fit)
        self.signal_selector.add_listener(self.update_fit)
        self.bg_selector.add_listener(self.update_fit)
        for key in ['conversion_factor', 'power_binning', 'power_x_axis', "channel"]:
            self.settings.get_lq(key).add_listener(self.update_fit)

        self.update_settings_min_max()

        fitters = [NonLinearityFitter()]
        try:
            from FoundryDataBrowser.viewers.plot_n_fit import LogisticFunctionFitter

            fitters.append(LogisticFunctionFitter())
        except ImportError:
            print("Warining LogisticFunctionFitter not loaded: pip install lmfit")
            pass

        self.plot_n_fit = PlotNFit(fitters)

        # UI
        self.ui = PowerScanUI(self.plot_n_fit)
        self.ui.add_to_select_layout(
            self.settings.New_UI(exclude=('info', 'ignore')))
        self.ui.add_to_select_layout(self.bg_selector.New_UI())
        self.ui.add_to_select_layout(self.signal_selector.New_UI())
        self.signal_selector.set_plot_data_item(self.ui.spec_line)
        self.bg_selector.set_plot_data_item(self.ui.spec_line)

        #
        commit_widget = QtWidgets.QWidget()
        commit_layout = QtWidgets.QVBoxLayout(commit_widget)
        self.ui.add_to_select_layout(commit_widget)
        commit_layout.addWidget(
            self.settings.New_UI(include=('info', 'ignore')))
        pb = QtWidgets.QPushButton('commit_params')
        pb.clicked.connect(self.commit_params)
        commit_layout.addWidget(pb)
        pb = QtWidgets.QPushButton('load params')
        pb.clicked.connect(self.update_params_from_json)
        commit_layout.addWidget(pb)
        pb = QtWidgets.QPushButton('new notebook')
        pb.clicked.connect(self.new_notebook)
        commit_layout.addWidget(pb)
        pb = QtWidgets.QPushButton('run with config')
        pb.clicked.connect(self.plot_config)
        commit_layout.addWidget(pb)


        # pb = QtWidgets.QPushButton('launch notebook')
        # pb.clicked.connect(self.launch_lab)
        # commit_layout.addWidget(pb)

    def update_hyperspec(self):
        self.wls = np.arange(512)
        self.spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
        self.power_arrays = {"pm_powers": np.arange(21)}

    def get_bg(self):
        S = self.settings
        if self.bg_selector.activated.val:
            return self.bg_selector.select(self.spectra[:, S["channel"], :], -1).mean()
        else:
            return 0

    def get_dependence_data(self):
        S = self.settings
        data = self.signal_selector.select(
            self.spectra[:, S["channel"], :], -1)
        binning = S["power_binning"]
        if binning > 1:
            Np, ns = data.shape
            data = (
                data[: (Np // binning) * binning, :]
                .reshape(-1, binning, ns)
                .mean(axis=1)
            )
        y = data.sum(axis=-1) - self.get_bg()

        x = self.power_arrays[self.settings["power_x_axis"]]
        binning = self.settings["power_binning"]
        if binning > 1:
            x = x[: (len(x) // binning) *
                  binning].reshape(-1, binning).mean(-1)

        x = x * self.settings["conversion_factor"]

        # only positive values
        mask = (y > 0) * (x > 0)
        return x[mask], y[mask]

    def update_spec_plot(self):
        S = self.settings
        y = self.spectra[S["spec_index"], S["channel"], :]
        self.ui.spec_line.setData(x=self.wls, y=y)

        print(self.wls)
        self.update_target()

    def update_target(self):
        S = self.settings
        ii = int(S["spec_index"] / S["power_binning"])
        x, y = self.get_dependence_data()
        pos = self.power_arrays["power_wheel_position"][ii]
        power = self.power_arrays["pm_powers"][ii]
        text = f"wheel {pos}\n power {power}\n counts {y[ii]}"
        self.ui.set_target(x[ii], y[ii], text)

    def update_fit(self):
        x, y = self.get_dependence_data()
        self.plot_n_fit.set_data(x, y, 0, False)
        self.plot_n_fit.update()
        self.update_target()

    def on_change_data_filename(self, fname=None):
        self.fname = fname

        try:
            self.spectra, self.power_arrays, self.aquisition_type, self.sample, self.wls = load_file(
                fname, self.power_x_axis_choices)

            if self.spectra.shape[-1] <= 1:  # no spectral dimension
                self.signal_selector.settings["activated"] = False
                self.bg_selector.settings["activated"] = False

            self.update_settings_min_max()

            self.ui.spec_plot.setTitle(self.aquisition_type)

            self.update_fit()

            self.update_params_from_json()

            self.databrowser.ui.statusbar.showMessage(
                "loaded:{}\n".format(fname))

        except Exception as err:
            self.databrowser.ui.statusbar.showMessage(
                "failed to load {}:\n{}".format(fname, err)
            )

    def update_settings_min_max(self):
        Np, N_channel, N_wls = self.spectra.shape
        S = self.settings
        S.spec_index.change_min_max(-Np, Np - 1)
        S.channel.change_min_max(0, N_channel - 1)
        S.power_binning.change_min_max(1, Np)
        if N_wls == 1:
            self.bg_selector.activated.update_value(False)

    def new_notebook(self):
        import shutil
        shutil.copyfile(self.notebook_file_original, self.notebook_file_target)

    def plot_config(self):
        from .power_scans_h5_configured_plot import run
        run(self.json_file, self.dir_fname)


    # def launch_lab(self):
    #     import os
    #     directory = os.path.dirname(self.fname)
    #     if directory != "":
    #         #import subprocess
    #         #from subprocess import Popen, PIPE
    #         #process = Popen(['cmd', f'jupyter lab --notebook-dir {directory}'], stdout=PIPE, stderr=PIPE)
    #         #stdout, stderr = process.communicate()
    #         #subprocess.call(['cmd', f'jupyter lab --notebook-dir {directory}'])
    #         os.system(f'jupyter lab --notebook-dir {directory}')
    #     else:
    #         print('select a file first')


def load_file(fname, power_x_axis_choices=("pm_powers", "pm_powers_after", "power_wheel_position")):
    import h5py
    with h5py.File(fname, "r") as h5file:
        if "sample" in h5file["app/settings"].attrs.keys():
            sample = h5file["app/settings"].attrs["sample"]
        if "measurement/power_scan_df" in h5file:
            H = h5file["measurement/power_scan_df"]
        else:
            H = h5file["measurement/power_scan"]

        # # Provide wls and spectra
        # wls has shape (N_wls,) [dim=1]
        # spectra has shape (Np, N_channels, N_wls).
        #    E.g. with Np=21 and N_wls=512:
        wls = np.arange(512)
        spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
        # If present override acq_times_array which will be used
        # to normalize to counts per second:
        acq_times_array = [None]

        aquisition_type = (
            "No data found"  # some info text that will be shown in the title
        )

        if "integrated_spectra" in H:
            for k in H.keys():
                if "acq_times_array" in k:
                    acq_times_array = H[k][:]
            wls = H["wls"][:]
            spectra = H["spectra"][:].reshape(-1, 1, len(wls))
            aquisition_type = "Spectrum"

        for harp in ["picoharp", "hydraharp"]:
            if "{}_histograms".format(harp) in H:
                histograms = H["{}_histograms".format(harp)][:]
                acq_times_array = H["{}_elapsed_time".format(harp)][:]
                wls = H["{}_time_array".format(harp)][:]
                if np.ndim(histograms) == 2:
                    histograms = histograms.reshape(-1, 1, len(wls))
                spectra = histograms
                aquisition_type = harp

        if "apd_count_rates" in H:
            apd_count_rates = H["apd_count_rates"][:]
            spectra = apd_count_rates.reshape((-1, 1, 1))
            aquisition_type = "APD"
            wls = np.arange(spectra.shape[-1])

        if "thorlabs_powermeter_2_powers" in H:
            powers_y = H["thorlabs_powermeter_2_powers"][:]
            spectra = powers_y.reshape((-1, 1, 1))
            aquisition_type = "power_meter_2"
            wls = np.arange(spectra.shape[-1])

        Np = spectra.shape[0]
        if np.any(acq_times_array == None):
            spectra = (1.0 * spectra.T / acq_times_array).T
        else:
            spectra = 1.0 * spectra  # ensure floats

        # if scan was no completed the power arrays will be chopped
        # get power arrays
        power_arrays = {}
        for key in power_x_axis_choices:
            try:
                power_arrays.update({key: H[key][:Np]})
            except:
                pass

        if Np != len(H["pm_powers"][:]):
            aquisition_type = "[INTERRUPTED Scan] " + \
                aquisition_type

    return spectra, power_arrays, aquisition_type, sample, wls
