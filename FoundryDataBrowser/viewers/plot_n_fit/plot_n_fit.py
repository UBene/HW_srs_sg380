'''
Created on Aug 3, 2019

@author: Benedikt Ursprung
'''

import numpy as np
from ScopeFoundry.logged_quantity import LQCollection
from qtpy import QtGui  # used for clipboard 
from FoundryDataBrowser.viewers.plot_n_fit.pgwidget import PlotNFitPGDockArea


class PlotNFit:
    '''        
    add fitters of type <BaseFitter> (or more specific
    <LeastSquaresBaseFitter>):
    
    self.update_data(self, x, y, line_number=0, is_data_to_fit=True) 
        to plot data. 
        if flag is_data_to_fit is False use:
            self.update_data_to_fit(self, x, y)
                this allows the data to differ.
    '''

    def __init__(self,
                 fitters=[],
                 Ndata_lines=1,
                 colors=['w', 'r', 'b', 'y', 'm', 'c', 'g']):
        '''
        *fitters*      list of <BaseFitter> or <LeastSquaresBaseFitter>
        '''
        
        # Settings
        self.settings = LQCollection()
        self.fit_options = self.settings.New(
            'fit_options', str, choices=['DisableFit'], initial='DisableFit')

        # ui
        self.ui = PlotNFitPGDockArea(Ndata_lines, colors)              
        self.ui.add_to_settings_layout(self.settings.New_UI())
        self.ui.add_button('refit', self.update_fit)
        self.ui.add_button('clipboard plot', self.clipboard_plot)
        self.ui.add_button('clipboard results', self.clipboard_result)

        # fitters
        self.fitters = {}
        for fitter in fitters:
            self.add_fitter(fitter)

        self.update_data_to_fit(np.arange(4), np.arange(4))
        self.result_message = 'No fit results yet!'

        for lq in self.settings.as_list():
            lq.add_listener(self.on_change_fit_options)

        #self.on_change_fit_options()

    def add_fitter(self, fitter):
        self.fitters[fitter.name] = fitter
        self.ui.add_fitter_widget(fitter.name, fitter.ui)
        self.fit_options.add_choices(fitter.name)

    def on_change_fit_options(self):
        self.ui.activate_fitter_widget(self.fit_options.val)
        self.update_fit()

    def update_data(self, x, y, line_number=0, is_data_to_fit=True):
        self.ui.update_data_line(x, y, line_number)
        if is_data_to_fit:
            self.update_data_to_fit(x, y)
            self.update_fit()

    def update_data_to_fit(self, x, y):
        self.data_to_fit_x = x
        self.data_to_fit_y = y

    def update_fit(self):
        choice = self.fit_options.val
        enabled = choice != 'DisableFit'
        self.ui.fit_line.setVisible(enabled)
        if enabled:
            active_fitter = self.fitters[choice]
            self.fit = active_fitter.fit_xy(self.data_to_fit_x, self.data_to_fit_y)
            self.ui.update_fit_line(self.data_to_fit_x, self.fit)
            self.result_message = active_fitter.result_message
            self.ui.highlight_x_values(np.atleast_1d(active_fitter.highlight_x_vals))

    def fit_hyperspec(self, x, _hyperspec, axis=-1):
        choice = self.fit_options.val
        if self.fit_options.val == 'DisableFit':
            print('Warning!', self.state_info)
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
        if choice == 'DisableFit':
            return 'Plot&Fit disabled'
        else:
            return self.fitters[choice].state_info

    def get_result_table(self, decimals=3, include=None):
        choice = self.fit_options.val
        if choice == 'DisableFit':
            return 'Plot&Fit disabled'
        else:
            return self.fitters[choice].get_result_table(decimals, include)
        
    def clipboard_plot(self):
        import pyqtgraph.exporters as exp
        exporter = exp.SVGExporter(self.plot)   
        exporter.parameters()['scaling stroke'] = False
        exporter.export(copy=True)
        
    def clipboard_result(self):

        html_string = self.result_message
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_string, 'lxml')
        table = soup.find_all('table')[0]
        text = ''
        for line in table.findAll('tr'):
            for l in line.findAll('td'):
                print(l.getText())
                text += l.getText()        
        QtGui.QApplication.clipboard().setText(text)

