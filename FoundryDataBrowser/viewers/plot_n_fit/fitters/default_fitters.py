'''
Created on Mar 9, 2022

@author: bened
'''
from scipy.optimize import least_squares
from .base_fitter import BaseFitter


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
