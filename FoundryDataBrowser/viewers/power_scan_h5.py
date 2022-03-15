import pyqtgraph as pg
import h5py
from qtpy import QtWidgets
import numpy as np

import pyqtgraph.dockarea as dockarea

from ScopeFoundry.widgets import DataSelector
from ScopeFoundry.data_browser import DataBrowserView
from FoundryDataBrowser.viewers.plot_n_fit import (
    PlotNFit,
    LogisticFunctionFitter,
    PolyFitter,
)


class UI(dockarea.DockArea):
    def __init__(
        self, plot_n_fit,
    ):
        super().__init__()

        self.plot_n_fit = plot_n_fit

        self.data_select_widget = QtWidgets.QWidget()
        self.data_select_layout = QtWidgets.QHBoxLayout(self.data_select_widget)
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
        self.spec_line = self.spec_plot.plot([1, 2, 3, 4], [1, 3, 2, 4], pen="r")

        plot_n_fit.ui.settings_dock.setStretch(1, 2)
        self.fit_settings_dock = self.addDock(
            plot_n_fit.ui.settings_dock, "right", self.data_select_dock
        )

        self.scatter = pg.ScatterPlotItem([1], [1], pen="r")
        self.scatter_label = pg.TextItem(color="r")
        self.plot_n_fit.ui.plot.addItem(self.scatter)
        self.plot_n_fit.ui.plot.addItem(self.scatter_label)


class PowerScanH5View(DataBrowserView):

    name = "power_scan_h5"

    def is_file_supported(self, fname):
        return ("power_scan" in fname) and (".h5" in fname)

    def setup(self):

        # data format
        self.wls = np.arange(512)
        self.spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
        self.power_arrays = {
            "pm_powers": np.arange(21) / 2.1,
            "pm_powers_after": np.arange(21) / 2,
            "power_wheel_position": np.arange(21),
        }

        self.plot_n_fit = PlotNFit([LogisticFunctionFitter(), PolyFitter()])
        self.ui = UI(self.plot_n_fit)

        # settings
        self.settings.New("spec_index", dtype=int, initial=0)
        self.settings.New("channel", dtype=int, initial=0)
        self.power_x_axis_choices = (
            "pm_powers",
            "pm_powers_after",
            "power_wheel_position",
        )
        self.settings.New(
            "power_x_axis",
            dtype=str,
            initial="pm_powers",
            choices=self.power_x_axis_choices,
        )
        self.settings.New("power_binning", int, initial=1, vmin=1)
        self.settings.New("conversion_factor", float, initial=1.0)

        self.settings.spec_index.add_listener(self.update_spec_plot)
        self.settings.power_x_axis.add_listener(self.update_spec_plot)

        self.signal_selector = DataSelector(self.ui.spec_line, "signal select")
        self.bg_selector = DataSelector(self.ui.spec_line, "background select")

        self.signal_selector.add_listener(self.update_fit)
        self.bg_selector.add_listener(self.update_fit)

        for key in self.settings.keys():
            self.settings.get_lq(key).add_listener(self.update_fit)

        # more ui stuff
        self.ui.data_select_layout.addWidget(self.settings.New_UI())
        self.ui.data_select_layout.addWidget(self.bg_selector.New_UI())
        self.ui.data_select_layout.addWidget(self.signal_selector.New_UI())

        self.update_settings_min_max()

    def update_hyperspec(self):
        self.wls = np.arange(512)
        self.spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
        self.power_arrays = {"pm_powers": np.arange(21)}

    def get_bg(self):
        if self.bg_selector.activated.val:
            s = np.s_[:, self.settings["channel"], self.bg_selector.slice]
            return self.spectra[s].sum()
        else:
            return 0

    def get_dependence_data(self):
        s = np.s_[:, self.settings["channel"], self.signal_selector.slice]
        data = self.spectra[s]
        binning = self.settings["power_binning"]
        if binning > 1:
            Np, ns = data.shape
            data = (
                data[: (Np // binning) * binning, :]
                .reshape(-1, binning, ns)
                .mean(axis=1)
            )
        y = self.spectra[s].sum(axis=-1) - self.get_bg()

        x = self.power_arrays[self.settings["power_x_axis"]]
        binning = self.settings["power_binning"]
        if binning > 1:
            x = x[: (len(x) // binning) * binning].reshape(-1, binning).mean(-1)

        return x * self.settings["conversion_factor"], y

    def update_spec_plot(self):
        S = self.settings
        y = self.spectra[S["spec_index"], S["channel"], :]
        self.ui.spec_line.setData(self.wls, y)

    def update_fit(self):
        print(self.name, "update_fit")
        x, y = self.get_dependence_data()
        self.plot_n_fit.update_data(x, y, 0, False)
        self.plot_n_fit.update()

        S = self.settings
        ii = int(S["spec_index"] / S["power_binning"])
        self.ui.scatter.setData(x=(x[ii],), y=(y[ii],))
        self.ui.scatter_label.setPos(x[ii], y[ii])
        pos = self.power_arrays["power_wheel_position"][ii]
        power = self.power_arrays["pm_powers"][ii]
        self.ui.scatter_label.setText(f"wheel {pos}\n power {power}")

    def on_change_data_filename(self, fname=None):
        try:
            self.h5file = h5py.File(fname, "r")

            self.sample = ""
            if "sample" in self.h5file["app/settings"].attrs.keys():
                self.sample = self.h5file["app/settings"].attrs["sample"]
            if self.sample == "":
                self.sample = "<->"
            print("sample string", self.sample)

            if "measurement/power_scan_df" in self.h5file:
                H = self.h5file["measurement/power_scan_df"]
            else:
                H = self.h5file["measurement/power_scan"]

            # # Provide self.wls and self.spectra
            # self.wls has shape (N_wls,) [dim=1]
            # self.spectra has shape (Np, N_channels, N_wls).
            #    E.g. with Np=21 and N_wls=512:
            self.wls = np.arange(512)
            self.spectra = 0.5 * np.arange(512 * 21 * 1).reshape((21, 1, 512))
            # If present override acq_times_array which will be used
            # to normalize to counts per second:
            acq_times_array = [None]

            self.aquisition_type = (
                "No data found"  # some info text that will be shown in the title
            )

            if "integrated_spectra" in H:
                for k in H.keys():
                    if "acq_times_array" in k:
                        acq_times_array = H[k][:]
                self.wls = H["wls"][:]
                self.spectra = H["spectra"][:].reshape(-1, 1, len(self.wls))
                self.aquisition_type = "Spectrum"

            for harp in ["picoharp", "hydraharp"]:
                if "{}_histograms".format(harp) in H:
                    histograms = H["{}_histograms".format(harp)][:]
                    acq_times_array = elapsed_time = H["{}_elapsed_time".format(harp)][
                        :
                    ]
                    self.wls = H["{}_time_array".format(harp)][:]
                    if np.ndim(histograms) == 2:
                        histograms = histograms.reshape(-1, 1, len(self.wls))
                    self.spectra = histograms
                    self.aquisition_type = harp

            if "apd_count_rates" in H:
                self.spec_x_slicer.settings["activated"] = False
                self.bg_slicer.settings["activated"] = False
                apd_count_rates = H["apd_count_rates"][:]
                self.spectra = apd_count_rates.reshape((-1, 1, 1))
                self.aquisition_type = "APD"

            if "thorlabs_powermeter_2_powers" in H:
                self.spec_x_slicer.settings["activated"] = False
                self.bg_slicer.settings["activated"] = False
                powers_y = H["thorlabs_powermeter_2_powers"][:]
                self.spectra = powers_y.reshape((-1, 1, 1))
                self.aquisition_type = "power_meter_2"

            Np = self.spectra.shape[0]
            if np.any(acq_times_array == None):
                self.spectra = (1.0 * self.spectra.T / acq_times_array).T
            else:
                self.spectra = 1.0 * self.spectra  # ensure floats

            # if scan was no completed the power arrays will be chopped
            # get power arrays
            self.power_arrays = {}
            for key in self.power_x_axis_choices:
                try:
                    self.power_arrays.update({key: H[key][:Np]})
                except:
                    pass

            if Np != len(H["pm_powers"][:]):
                self.aquisition_type = "[INTERRUPTED Scan] " + self.aquisition_type

            self.h5file.close()

            self.databrowser.ui.statusbar.showMessage("loaded:{}\n".format(fname))

            self.update_settings_min_max()

            self.ui.spec_plot.setTitle(self.aquisition_type)

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
