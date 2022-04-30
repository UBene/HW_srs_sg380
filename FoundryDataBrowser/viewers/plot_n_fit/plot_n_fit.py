"""
Created on Aug 3, 2019

@author: Benedikt Ursprung
"""

import numpy as np
from ScopeFoundry.logged_quantity import LQCollection
from FoundryDataBrowser.viewers.plot_n_fit.pgwidget import PlotNFitPGDockArea
from .fitters.base_fitter import BaseFitter
from ScopeFoundry.widgets import DataSelector


class PlotNFit:
    """        
    provides a ui <PlotNFitPGDockArea> and plotter

    methods:
        set_data(self, x, y, line_number=0, is_data_to_fit=True)
    """

    def __init__(
        self,
        fitters: [BaseFitter()] = [],
        Ndata_lines=1,
        colors=["w", "r", "b", "y", "m", "c", "g"],
    ):
        """
        *fitters*      list <BaseFitter> instances 
                       for new fitter I recommend inheritance of
                       <LeastSquaresBaseFitter> or <LmFitBaseFitter>
        """

        self.ready = False
        self._data = [[(1, 2, 3), (0.1, 2, 1)]] * Ndata_lines

        # Settings
        self.settings = LQCollection()
        self.fit_options = self.settings.New(
            "fit_options", str, choices=["DisableFit"], initial="DisableFit"
        )

        # ui
        self.ui = PlotNFitPGDockArea(Ndata_lines, colors)
        self.ui.add_to_settings_layout(self.settings.New_UI())
        self.ui.add_button("refit", self.update_fit)
        self.ui.add_button("clipboard plot", self.ui.clipboard_plot)
        self.ui.add_button("clipboard results", self.clipboard_result)

        # fitters
        self.fitters = {}
        for fitter in fitters:
            self.add_fitter(fitter)

        self.set_data_to_fit(np.arange(4), np.arange(4))
        self.result_message = "No fit results yet!"

        for lq in self.settings.as_list():
            lq.add_listener(self.on_change_fit_options)


        self.plot_masker = DataSelector(
            self.ui.data_lines[0], name="plot_masker"
            )
        self.ui.add_to_settings_layout(self.plot_masker.New_UI())
        

        self.data_selector = DataSelector(
            self.ui.data_lines[0], name="selector")
        self.data_selector.add_listener(self.update)
        self.ui.add_to_settings_layout(self.data_selector.New_UI())
                
        self.active_line = 0
        self.on_change_fit_options()
        self.ready = True

    def add_fitter(self, fitter: BaseFitter):
        self.fitters[fitter.name] = fitter
        self.ui.add_fitter_widget(fitter.name, fitter.ui)
        self.fit_options.add_choices(fitter.name)

    def update(self):
        if self.ready:
            self.update_data_to_fit(self.active_line)
            self.update_fit()

    def on_change_fit_options(self):
        self.ui.activate_fitter_widget(self.fit_options.val)
        self.update()

    def set_data(self, x, y, line_number=0, is_data_to_fit=False):
        self.active_line = line_number
        self._data[line_number] = [x, y]
        self.ui.update_data_line(x, y, line_number)
        self.data_selector.on_change_start_stop()
        if is_data_to_fit:
            self.update_fit()
        self.plot_masker.on_change_start_stop()
        
    def set_data_to_fit(self, x, y):
        self.data_to_fit_x = x
        self.data_to_fit_y = y

    def update_data_to_fit(self, line_number=0):
        data = self.data_selector.select_XY(self._data[line_number])
        self.set_data_to_fit(*data)

    def update_fit(self):
        choice = self.fit_options.val
        enabled = choice != "DisableFit"
        self.ui.fit_line.setVisible(enabled)
        self.ui.update_select_line(self.data_to_fit_x, self.data_to_fit_y)

        if enabled:
            active_fitter = self.fitters[choice]
            try:
                self.fit = active_fitter.fit_xy(
                    self.data_to_fit_x, self.data_to_fit_y)
                self.ui.update_fit_line(self.data_to_fit_x, self.fit)
                self.result_message = active_fitter.result_message
                self.ui.highlight_x_values(
                    np.atleast_1d(active_fitter.highlight_x_vals))
                self.data_selector.set_label(active_fitter.get_resuts_html())
            except (ZeroDivisionError,):
                pass
        else:
            self.ui.clear()

    def fit_hyperspec(self, x, _hyperspec, axis=-1):
        choice = self.fit_options.val
        if self.fit_options.val == "DisableFit":
            print("Warning!", self.state_info)
        else:
            F = self.fitters[choice]
            Res = F.fit_hyperspec(x, _hyperspec, axis=axis)
            Descriptions = F.hyperspec_descriptions()
            return [Descriptions, Res]

    def get_docks_as_dockarea(self):
        return self.ui

    @property
    def state_info(self):
        choice = self.fit_options.val
        if choice == "DisableFit":
            return "Plot&Fit disabled"
        else:
            return self.fitters[choice].state_info

    def get_result_table(self, decimals=3, include=None):
        choice = self.fit_options.val
        if choice == "DisableFit":
            return "Plot&Fit disabled"
        else:
            return self.fitters[choice].get_result_table(decimals, include)

    def clipboard_result(self):

        html_string = self.result_message
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_string, "lxml")
        table = soup.find_all("table")[0]
        text = ""
        for line in table.findAll("tr"):
            for l in line.findAll("td"):
                text += l.getText()

        self.ui.set_clipboard_text(text)

    def get_configs(self):
        configs = {name: lq.value for name,
                  lq in self.settings.as_dict().items()}
        for k, v in self.fitters.items():
            configs[k] = v.get_configs()
        configs['data_selector'] = self.data_selector.get_configs()
        configs['plot_masker'] = self.plot_masker.get_configs()
        return configs

    def set_configs(self, configs):
        for name, lq in self.settings.as_dict().items():
            lq.update_value(configs.get(name, lq.value))
        for k, v in self.fitters.items():
            v.set_configs(configs[k])
        self.data_selector.set_configs(configs['data_selector'])
        self.plot_masker.set_configs(configs['plot_masker'])
