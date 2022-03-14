"""
Created on Mar 14, 2022

@author: Benedikt Ursprung
"""
from scipy.optimize import least_squares
import numpy as np
from .base_fitter import BaseFitter


class LeastSquaresBaseFitter(BaseFitter):
    """ 
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
    """

    fit_params = {}
    name = "least_square_base_fitter"

    def func(self, params, x):
        """Override! This is the fit function!"""
        raise NotImplementedError(self.name + " needs a fit function")

    def _residuals(self, params, x, data):
        return self.func(params, x) - data

    def fit_xy(self, x, y):

        t = x - x.min()

        res = least_squares(
            fun=self._residuals,
            bounds=self.bounds_array,
            x0=self.initials_array,
            args=(t, y),
        )

        self.update_fit_results(res.x, res.message + f"<br>nfval:{res.nfev}")

        fit = self.func(res.x, t)
        return fit

    def fit_hyperspec(self, t, _hyperspec, axis=-1):
        def f(y, t):
            res = least_squares(
                fun=self._residuals,
                bounds=self.bounds_array,
                x0=self.initials_array,
                args=(t, y),
            )
            return res.x

        fit = np.apply_along_axis(f, axis, _hyperspec, t=t - t.min())
        return np.rollaxis(fit, axis)


class MonoExponentialFitter(LeastSquaresBaseFitter):

    fit_params = [
        ["A0", (1.0, 0.0, 1e10)],
        ["tau0", (1.0, 0.0, 1e10)],
    ]

    name = "mono_exponential"

    def func(self, params, x):
        return params[0] * np.exp(-x / params[1])


class BiExponentialFitter(LeastSquaresBaseFitter):

    fit_params = [
        ["A0", (1.0, 0.0, 1e10)],
        ["tau0", (1.0, 0.0, 1e10)],
        ["A1", (1.0, 0.0, 1e10)],
        ["tau1", (9.9, 0.0, 1e10)],
    ]

    name = "bi_exponetial"

    def func(self, params, x):
        return params[0] * np.exp(-x / params[1]) + params[2] * np.exp(-x / params[3])

    def add_derived_result_quantities(self):
        self.derived_results.New("tau_m", float, initial=10, unit="ns")
        self.derived_results.New("A0_pct", float, initial=10, unit="%")
        self.derived_results.New("A1_pct", float, initial=10, unit="%")

    def process_results(self, fit_results):
        A0, tau0, A1, tau1 = fit_results
        A0, tau0, A1, tau1 = sort_biexponential_components(A0, tau0, A1, tau1)

        A0_norm, A1_norm = A0 / (A0 + A1), A1 / (A0 + A1)
        tau_m = A0_norm * tau0 + A1_norm * tau1

        # update derived results
        D = self.derived_results
        D["tau_m"] = tau_m
        D["A0_pct"] = A0_norm * 100
        D["A1_pct"] = A1_norm * 100
        return (A0, tau0, A1, tau1)

    def fit_hyperspec(self, t, _hyperspec, axis=-1):
        A0, tau0, A1, tau1 = LeastSquaresBaseFitter.fit_hyperspec(
            self, t, _hyperspec, axis=axis
        )
        A0, tau0, A1, tau1 = sort_biexponential_components(A0, tau0, A1, tau1)

        A0_norm, A1_norm = A0 / (A0 + A1), A1 / (A0 + A1)
        tau_m = A0_norm * tau0 + A1_norm * tau1

        return np.array([A0_norm, tau0, A1_norm, tau1, tau_m])

    def hyperspec_descriptions(self):
        return LeastSquaresBaseFitter.hyperspec_descriptions(self) + ["taum"]


def sort_biexponential_components(A0, tau0, A1, tau1):
    """
    ensures that tau0 < tau1, also swaps values in A1 and A0 if necessary.
    """
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
