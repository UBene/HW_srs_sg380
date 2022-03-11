'''
Created on Aug 3, 2019

@author: Benedikt Ursprung
'''

import pyqtgraph as pg
import pyqtgraph.dockarea as dockarea

import numpy as np
from ScopeFoundry.logged_quantity import LQCollection, LoggedQuantity
from qtpy import QtWidgets, QtGui


class PlotNFitPGDockArea(dockarea.DockArea):
    '''
    ui for plotNFit that provides
        1. setting_dock
        2. graph_dock with fit_line and data_lines
    '''
    
    def __init__(self,
                 Ndata_lines=0,
                 pens=['w']):
        super().__init__()
        
        self.settings_ui = QtWidgets.QWidget()
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_ui.setLayout(self.settings_layout)
        self.settings_dock = dockarea.Dock(name='Fit Settings', widget=self.settings_ui)
        self.addDock(self.settings_dock)
        VSpacerItem = QtWidgets.QSpacerItem(0, 0,
                                            QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.settings_layout.addItem(VSpacerItem)
        
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot()
        self.graph_dock = dockarea.Dock(name='Graph Plot', widget=self.graph_layout)        
        self.addDock(self.graph_dock, position='right', relativeTo=self.settings_dock)        
        self.settings_dock.setStretch(1, 1)

        self.data_lines = []
        for i in range(Ndata_lines):
            self.data_lines.append(self.plot.plot(y=[0, 2, 1, 3, 2], pen=pens[i])) 
        self.fit_line = self.plot.plot(y=[0, 2, 1, 3, 2], pen='g') 

        self.fitter_widgets = {}
        self.reset_highlight_x_values()
        
    def reset_highlight_x_values(self):
        if hasattr(self, 'vertical_lines'):
            for l in self.vertical_lines:
                self.plot.removeItem(l)
                l.deleteLater()
        self.vertical_lines = []
        
    def highlight_x_values(self, values):
        self.reset_highlight_x_values()
        pen = 'g'

        for x in values:
            l = pg.InfiniteLine(
                pos=(x, 0),
                movable=False,
                angle=90,
                pen=pen,
                label='{value:0.2f}',
                labelOpts={
                    'color': pen,
                    'movable': True,
                    'fill': (200, 200, 200, 100)
                })
            self.plot.addItem(l)
            self.vertical_lines.append(l)
            
    def update_fit_line(self, x, y):
        self.fit_line.setData(x, y)
        
    def update_data_line(self, x, y, line_number=0):
        self.data_lines[line_number].setData(x, y)    
        
    def add_to_settings_layout(self, widget):
        n = self.settings_layout.count() - 1
        self.settings_layout.insertWidget(n, widget)
        
    def add_button(self, name, callback_func):
        PB = QtWidgets.QPushButton(name)
        PB.clicked.connect(callback_func)
        self.add_to_settings_layout(PB)
        
    def add_fitter_widget(self, name, widget):
        self.fitter_widgets[name] = widget
        widget.setVisible(False)
        self.add_to_settings_layout(widget)
        
    def activate_fitter_widget(self, name:str):
        for k, widget in self.fitter_widgets.items():
            widget.setVisible(k == name)


class PlotNFit:
    '''        
    add fitters of type <BaseFitter> (or more specific
    <LeastSquaresBaseFitter>):
    
    self.update_data(self, x, y, line_number=0, is_data_to_fit=True) 
        to plot data. 
        if flag is_data_to_fit is False use:
            update_fit_data(self, x_fit_data, y_fit_data)
                this allows the data to differ.
    '''

    def __init__(self,
                 fitters=[],
                 Ndata_lines=1,
                 pens=['g', 'w', 'r', 'b', 'y', 'm', 'c']):
        '''
        *fitters*      list of <BaseFitter> or <LeastSquaresBaseFitter>
        '''

        self.pens = pens
        
        # Settings
        self.settings = LQCollection()
        self.fit_options = self.settings.New(
            'fit_options', str, choices=['DisableFit'], initial='DisableFit')

        # ui
        self.ui = PlotNFitPGDockArea(Ndata_lines, pens)              
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

        self.on_change_fit_options()

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

    
class FitterQWidget(QtWidgets.QWidget):
    ''' ui widget for  BaseFitter'''
    
    def __init__(self):
        super().__init__()
        self.layout = layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.result_label = QtWidgets.QLabel()
        layout.addWidget(self.result_label)
    
    def add_collection_widget(self, collection, title):
        self.layout.addWidget(QtWidgets.QLabel(f'<h3>{title}</h3>'))
        widget = collection.New_UI()
        self.layout.addWidget(widget)
        return widget
        
    def add_enabable_collection_widget(self, collection:LQCollection,
                                       title:str,
                                       enable_setting:LoggedQuantity):
        widget = self.add_collection_widget(collection, title)
        enable_setting.add_listener(widget.setEnabled)
        
    def add_button(self, name, callback_func):
        PB = QtWidgets.QPushButton(name)
        self.layout.addWidget(PB)
        PB.clicked.connect(callback_func)
        
    def set_result_label(self, text):
        self.result_label.setText(text)
        
    
class BaseFitter:
    '''    
        *fit_params* list of parameters to be optimized and associated values: 
                     [
                     ['ParamName0', (initial0, lower_bound0, upper_bound0)] 
                     ['ParamName1', (initial1, lower_bound1, upper_bound1)]
                     ...'
                     ] 
                        
        *name*       any string 
        
        Implement `fit_xy(x,y)`
        
        <LeastSquaresBaseFitter> might be easier to use.
        
        other useful function to override:
            process_results
            add_derived_result_quantities
    '''

    fit_params = []
    name = 'xy_base_fitter'

    def __init__(self):

        self.fit_results = LQCollection()
        self.derived_results = LQCollection()
        self.settings = LQCollection()
        self.initials = LQCollection()
        self.bounds = LQCollection()

        for name, init in self.fit_params:
            self.fit_results.New(name, initial=0.0)
            if init is None:
                continue
            if len(init) == 3:
                (val, lower, upper) = init
                self.bounds.New(name + "_lower", initial=lower)
                self.bounds.New(name + "_upper", initial=upper)
                self.initials.New(name, initial=val)

        self.use_bounds = self.settings.New('use_bounds', bool, initial=False)

        self.add_derived_result_quantities()
        self.add_settings_quantities()

        self.ui = FitterQWidget()
        self.ui.add_collection_widget(self.settings, 'settings')
        self.ui.add_collection_widget(self.initials, 'initials')
        self.ui.add_enabable_collection_widget(self.bounds, 'bounds', self.use_bounds)

        self.ui.add_button('initials from results',
                self.set_initials_from_results)

        self.result_message = self.name + ': result_message message not set yet'

        self.highlight_x_vals = []  # just a container for x_values that can be used

    def fit_xy(self, x:np.array, y:np.array) -> np.array:
        ''' 
        has to return an array with the fit of len(y)
        recommended properties/functions to use:
            
            self.initials_array
            self.bounds_array
            
            self.update_fit_results(fit_results, additional_msg) 
                [recommended if the number of fit_params is fixed]
                otherwise pass a string to self.set_result_message(message)
                
            return fit #this 
        '''
        raise NotImplementedError()

    def update_fit_results(self, fit_results, additional_msg=''):
        '''
        helper function, which updates the results
        quantitiy collection and sets the result_message.
        the order of *results_array* is the 
        same as the order the parameters were defined.        
        Note: this function calls self.process_results
        before updating the results table.
                    
        alternatively pass a string to set_result_message(message)
        '''
        processed_fit_results = self.process_results(fit_results)
        for val, lq in zip(processed_fit_results, self.fit_results.as_list()):
            lq.update_value(val)
            
        res_table = self.get_result_table(decimals=3)
        header = ['param', 'value', 'unit']
        html_table = _table2html(res_table, header=header)
        if additional_msg != 0:
            msg = html_table + f'<p margin-top=5px>{additional_msg}</p>' 
            self.set_result_message(msg)
        else:
            self.set_result_message(html_table)

    def add_derived_result_quantities(self):
        '''add results other than fit_params eg: 
        self.derived_results.New('resX', ...), 
        use `process_results` to update this quantities!
        '''
        pass

    def process_results(self, fit_results):
        '''
        calculate and set derived_results here, this function will be called
        in update_fit_results. The fit_results quantities are set according 
        to the output of this function. 
        Hence this function has to return the (processed) fit results in the 
        correct order, that the order they were defined in fit_params.       
        '''
        processed_fit_results = fit_results
        return processed_fit_results

    def add_settings_quantities(self):
        '''
        add results other than fit_params e.g: self.results.New('resX', ...), 
        set them in process_results
        '''
        pass

    @property
    def bounds_array(self):
        '''returns least_square style bounds array'''
        if self.settings['use_bounds']:
            f = filter(lambda lq: lq.name.endswith('lower'),
                       self.bounds.as_list())
            lower_bounds = [lq.val for lq in f]
            f = filter(lambda lq: lq.name.endswith('upper'),
                       self.bounds.as_list())
            upper_bounds = [lq.val for lq in f]
        else:
            N_bound_pairs = len(self.initials.as_list())
            lower_bounds = [-np.inf] * N_bound_pairs
            upper_bounds = [np.inf] * N_bound_pairs
        return np.array([lower_bounds, upper_bounds])

    @property
    def derived_results_array(self):
        return np.array([lq.val for lq in self.derived_results.as_list()])

    @property
    def fit_results_array(self):
        return np.array([lq.val for lq in self.fit_results.as_list()])

    @property
    def initials_array(self):
        return np.array([lq.val for lq in self.initials.as_list()])

    def hyperspec_descriptions(self):
        '''overwrite these if the results of fit_hyperspec is not
        fully described by fit_params!'''
        return [self.name + '_' + lq.name for lq in self.fit_results.as_list()]

    def fit_hyperspec(self, t, _hyperspec, axis=-1):
        '''
        intended for multidimensional arrays.
        Convention: this function should fit along *axis* and should 
                    return the params along the 0th axis! 
        '''
        raise NotImplementedError(self.name + 
                                  '_fit_hyperspec() not implemented')

    def get_result_table(self, decimals=3, include=None):
        res_table = []
        for lq in list(self.fit_results.as_list()) + list(
                self.derived_results.as_list()):
            if include == None or lq.name in include:
                q = lq.name
                val = ('{:4.{prec}f}'.format(lq.val, prec=decimals))
                if lq.unit is not None:
                    unit = '{}'.format(lq.unit)
                else:
                    unit = ''
                res_table.append([q, val, unit])
        return res_table

    def set_result_message(self, message):
        self.result_message = message
        self.ui.set_result_label('<h3>results</h3>' + self.result_message)

    def set_initials_from_results(self):
        for k in self.initials.as_dict().keys():
            self.initials[k] = self.fit_results[k]

    @property
    def state_info(self):
        return self.name + self.state_description()

    def state_description(self):
        return ''


def _table2html(data_table,
                header=[],
                markup='border="0" alignment="center", cellspacing="2"'):
    if len(data_table) == 0: return ''
    text = f'<table {markup}>'
    if len(header) == len(data_table[0]):
        text += '<tr align="left">'
        for element in header:
            text += '<th>{} </th>'.format(element)
        text += '</tr>'
    for line in data_table:
        text += '<tr>'
        for element in line:
            text += '<td>{} </td>'.format(element)
        text += '</tr>'
    text += '</table>'
    return text


from scipy.optimize import least_squares


class LeastSquaresBaseFitter(BaseFitter):
    ''' 
    wrapper scipy.otimize.least_squares and 
        
        *fit_params* list of parameters to be optimized and associated values: 
                     [
                     ['ParamName0', (initial0, lower_bound0, upper_bound0)] 
                     ['ParamName1', (initial1, lower_bound1, upper_bound1)]
                     ...'
                     ] 

                        
        *name*       any string 
        
        Implement `func(params,x)`, 
            
        Note: x-x.min() is passed to least_squares(...)
    '''

    fit_params = {}
    name = 'least_square_base_fitter'

    def func(self, params, x):
        '''Override! This is the fit function!'''
        raise NotImplementedError(self.name + ' needs a fit function')

    def _residuals(self, params, x, data):
        return self.func(params, x) - data

    def fit_xy(self, x, y):

        t = x - x.min()

        res = least_squares(
            fun=self._residuals,
            bounds=self.bounds_array,
            x0=self.initials_array,
            args=(t, y))

        self.update_fit_results(res.x, res.message + f'<br>nfval:{res.nfev}')

        fit = self.func(res.x, t)
        return fit

    def fit_hyperspec(self, t, _hyperspec, axis=-1):

        def f(y, t):
            res = least_squares(
                fun=self._residuals,
                bounds=self.bounds_array,
                x0=self.initials_array,
                args=(t, y))
            return res.x

        fit = np.apply_along_axis(f, axis, _hyperspec, t=t - t.min())
        return np.rollaxis(fit, axis)


class TauXFitter(BaseFitter):

    fit_params = [ ['tau_x', None] ]

    name = 'tau_x'

    def fit_xy(self, x, y):

        t = x - x.min()

        tau = tau_x_calc(y - y[-3:].mean(), t)

        '''
        there is an inaccuracy from integrating over a finite time interval rather than
        to infinity. 
        '''
        decay_pct = (1 - y[-3:].mean() ** 2 / y[0:3].mean() ** 2) * 100  # should be 100%
        inaccuracy_pct = (1 - np.exp(-tau / t.max())) * 100  # should be 0
        
        msg1 = f'decay level: {decay_pct:0.1f}%'.rjust(100)
        msg2 = f'normalization inaccuracy: {inaccuracy_pct:0.1f}%'.rjust(100)
        self.update_fit_results([tau], msg1 + '<br>' + msg2)

        # Error from not integrating over 

        if tau == 0:  # handle wierd case so it doesn't crash
            return np.ones_like(y)
        return y[0:3].mean() * np.exp(-t / tau)

    def fit_hyperspec(self, x, _hyperspec, axis=-1):
        return tau_x_calc_map(x, _hyperspec, axis=axis)
    
    def hyperspec_descriptions(self):
        return ['tau_x']


def tau_x_calc(time_trace, time_array, X=0.6321205588300001):
    f = time_trace
    return time_array[ np.argmin((np.cumsum(f) / np.sum(f) - X) ** 2) ]


def tau_x_calc_map(time_array, time_trace_map, X=0.6321205588300001, axis=-1):
    kwargs = dict(time_array=time_array, X=X)
    return np.apply_along_axis(
        tau_x_calc, axis=axis, arr=time_trace_map, **kwargs)


class PolyFitter(BaseFitter):

    name = 'poly'

    def add_settings_quantities(self):
        self.settings.New('deg', int, initial=1)

    def transform(self, x, y):
        return x, y

    def inverse_transform(self, x, y):
        return x, y

    def fit_xy(self, x, y):
        deg = self.settings['deg']

        x_, y_ = self.transform(x, y)

        coefs = np.polynomial.polynomial.polyfit(x_, y_, deg)
        fit_ = np.polynomial.polynomial.polyval(x_, coefs)
        x, fit = self.inverse_transform(x, fit_)

        res_table = []
        header = ['coef', 'value']
        for i, c in enumerate(coefs):
            res_table.append([f'a{i}', "{:3.3f}".format(c)])

        html_table = _table2html(res_table, header)
        self.set_result_message(html_table)

        return fit

    def fit_hyperspec(self, x, _hyperspec, axis=-1):

        x_, h_ = self.transform(x, _hyperspec)

        # polyfit takes 2D array and fits along dim 0.
        h_ = h_.swapaxes(axis, 0)
        shape = h_.shape[1:]
        h_ = h_.reshape((len(x), -1))

        deg = self.settings['deg']
        coefs = np.polynomial.polynomial.polyfit(x_, h_, deg)
        Res = coefs.reshape(-1, *shape).swapaxes(0, axis)
        return Res

    def hyperspec_descriptions(self):
        return [f'a{i}' for i in range(self.settings['deg'])]


class SemiLogYPolyFitter(PolyFitter):

    name = 'semilogy_poly'

    def transform(self, x, y):
        return x, np.log(y)

    def inverse_transform(self, x, y):
        return x, np.exp(y)


class MonoExponentialFitter(LeastSquaresBaseFitter):

    fit_params = [ 
       ['A0', (1.0, 0.0, 1e10)],
       ['tau0', (1.0, 0.0, 1e10)],
    ]
    
    name = 'mono_exponential'

    def func(self, params, x):
        return params[0] * np.exp(-x / params[1])


class BiExponentialFitter(LeastSquaresBaseFitter):

    fit_params = [
        ['A0', (1.0, 0.0, 1e10)],
        ['tau0', (1.0, 0.0, 1e10)],
        ['A1', (1.0, 0.0, 1e10)],
        ['tau1', (9.9, 0.0, 1e10)],
    ]

    name = 'bi_exponetial'

    def func(self, params, x):
        return params[0] * np.exp(-x / params[1]) + params[2] * np.exp(
            -x / params[3])

    def add_derived_result_quantities(self):
        self.derived_results.New('tau_m', float, initial=10, unit='ns')
        self.derived_results.New('A0_pct', float, initial=10, unit='%')
        self.derived_results.New('A1_pct', float, initial=10, unit='%')

    def process_results(self, fit_results):
        A0, tau0, A1, tau1 = fit_results
        A0, tau0, A1, tau1 = sort_biexponential_components(A0, tau0, A1, tau1)

        A0_norm, A1_norm = A0 / (A0 + A1), A1 / (A0 + A1)
        tau_m = A0_norm * tau0 + A1_norm * tau1

        # update derived results
        D = self.derived_results
        D['tau_m'] = tau_m
        D['A0_pct'] = A0_norm * 100
        D['A1_pct'] = A1_norm * 100
        return (A0, tau0, A1, tau1)

    def fit_hyperspec(self, t, _hyperspec, axis=-1):
        A0, tau0, A1, tau1 = LeastSquaresBaseFitter.fit_hyperspec(
            self, t, _hyperspec, axis=axis)
        A0, tau0, A1, tau1 = sort_biexponential_components(A0, tau0, A1, tau1)

        A0_norm, A1_norm = A0 / (A0 + A1), A1 / (A0 + A1)
        tau_m = A0_norm * tau0 + A1_norm * tau1

        return np.array([A0_norm, tau0, A1_norm, tau1, tau_m])

    def hyperspec_descriptions(self):
        return LeastSquaresBaseFitter.hyperspec_descriptions(self) + ['taum']


def sort_biexponential_components(A0, tau0, A1, tau1):
    '''
    ensures that tau0 < tau1, also swaps values in A1 and A0 if necessary.
    '''
    A0 = np.atleast_1d(A0)
    tau0 = np.atleast_1d(tau0)
    A1 = np.atleast_1d(A1)
    tau1 = np.atleast_1d(tau1)
    mask = tau0 < tau1
    mask_ = np.invert(mask)
    new_tau0 = tau0.copy()
    new_tau0[mask_] = tau1[mask_]
    tau1[mask_] = tau0[mask_]
    new_A0 = A0.copy()
    new_A0[mask_] = A1[mask_]
    A1[mask_] = A0[mask_]
    try:
        new_A0 = np.asscalar(new_A0)
        new_tau0 = np.asscalar(new_tau0)
        A1 = np.asscalar(A1)
        tau1 = np.asscalar(tau1)
    except ValueError:
        pass
    return new_A0, new_tau0, A1, tau1  # Note, generally A1,tau1 were also modified.


class PeakUtilsFitter(BaseFitter):

    name = 'peakUtils'

    def add_settings_quantities(self):
        self.settings.New('baseline_deg', int, initial=0, vmin=-1, vmax=100)
        self.settings.New('thres', float, initial=0.5, vmin=0, vmax=1)
        self.settings.New('unique_solution', bool, initial=False)
        self.settings.New('min_dist', int, initial=-1)
        self.settings.New('gaus_fit_refinement', bool, initial=True)
        self.settings.New('ignore_phony_refinements', bool, initial=True)

    def fit_xy(self, x, y):

        PS = self.settings
        import peakutils
        base = 1.0 * peakutils.baseline(y, PS['baseline_deg'])

        if PS['min_dist'] < 0:
            min_dist = int(len(x) / 2)
        else:
            min_dist = PS['min_dist']
        peaks_ = peaks(y - base, x, PS['thres'], PS['unique_solution'],
                       min_dist, PS['gaus_fit_refinement'],
                       PS['ignore_phony_refinements'])

        peaks_ = np.atleast_1d(peaks_)
        self.highlight_x_vals = peaks_

        res_table = []
        header = ['peaks']
        for i, p in enumerate(peaks_):
            res_table.append(["{:3.3f}".format(p)])
        html_table = _table2html(res_table, header)
        self.set_result_message(html_table)

        # have to return something of len(x) to plot
        return base

    def fit_hyperspec(self, x, _hyperspec, axis=-1):
        PS = self.settings
        return peak_map(_hyperspec, x, axis, PS['thres'], int(len(x) / 2),
                        PS['gaus_fit_refinement'],
                        PS['ignore_phony_refinements'])

    def hyperspec_descriptions(self):
        return ['peak']

    def state_description(self):
        s = ''
        if self.settings['gaus_fit_refinement']:
            s += '_refined'
            if self.settings['ignore_phony_refinements']:
                s += '_ignored'
        return s


def peaks(spec,
          wls,
          thres=0.5,
          unique_solution=True,
          min_dist=-1,
          refinement=True,
          ignore_phony_refinements=True):
    import peakutils
    indexes = peakutils.indexes(spec, thres, min_dist=min_dist)
    if unique_solution:
        # we only want the highest amplitude peak here!
        indexes = [indexes[spec[indexes].argmax()]]

    if refinement:
        peaks_x = peakutils.interpolate(wls, spec, ind=indexes)
        if ignore_phony_refinements:
            for i, p in enumerate(peaks_x):
                if p < wls.min() or p > wls.max():
                    print(
                        'peakutils.interpolate() yielded result outside wls range, returning unrefined result'
                    )
                    peaks_x[i] = wls[indexes[i]]
    else:
        peaks_x = wls[indexes]

    if unique_solution:
        return peaks_x[0]
    else:
        return peaks_x


def peak_map(hyperspectral_data, wls, axis, thres, min_dist, refinement,
             ignore_phony_refinements):
    return np.apply_along_axis(
        peaks,
        axis,
        hyperspectral_data,
        wls=wls,
        thres=thres,
        unique_solution=True,
        min_dist=min_dist,
        refinement=refinement,
        ignore_phony_refinements=ignore_phony_refinements)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    W = PlotNFit(fitters=[
        # BiExponentialFitter(),
        MonoExponentialFitter(),
        TauXFitter(),
        PolyFitter(),
        # SemiLogYPolyFitter(),
        # PeakUtilsFitter(),
    ])

    app.setActiveWindow(W.ui)
    W.ui.show()

    # Test latest fitter:
    x = np.arange(1200) / 12
    y = np.exp(-x / 8.0) + 0.01 * np.random.rand(len(x))
    # y = x - 10 + 0.001 * np.random.rand(len(x))

    W.update_data(x, y)

    # x, y, = x[10:1100], y[10:1100]
    # W.update_fit_data(x, y)

    # hyperspec = np.array([y, y * 2, y * 3, y * 4, y * 5, y * 6]).reshape((3, 2, len(x)))

    # print(W.fit_hyperspec(x, hyperspec, -1))

    import sys
    sys.exit(app.exec())
