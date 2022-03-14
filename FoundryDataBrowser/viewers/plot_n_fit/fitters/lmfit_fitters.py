"""
Created on Mar 14, 2022

@author: Benedikt Ursprung
"""

from lmfit import Model
import numpy as np
from FoundryDataBrowser.viewers.plot_n_fit.fitters.base_fitter import BaseFitter
from FoundryDataBrowser.viewers.plot_n_fit.helper_functions import dict2htmltable


class LmfitBaseFitter(BaseFitter):
    def __init__(self):
        super().__init__()

    def func(self, x, **constants):
        """Override! This is the fit function!"""
        raise NotImplementedError(self.name + "func missing")

    @property
    def independent_vars(self):
        return ["x"]

    def make_model_params(self, model):
        params = model.make_params()
        for p in params:
            params[p].value = self.initials[p]
            params[p].init_value = self.initials[p]
            params[p].min = self.bounds[p + "_lower"]
            params[p].max = self.bounds[p + "_upper"]
            params[p].vary = self.vary[p]
        return params

    def fit_xy(self, x: np.array, y: np.array) -> np.array:

        model = Model(self.func, independent_vars=self.independent_vars)
        params = self.make_model_params(model)
        res = model.fit(y, params, x=x)
        fit = self.func(x, **res.values)

        self.set_result_message(res.message + dict2htmltable(res.values))
        self.update_fit_results(res.values.values())
        return fit


def logistic_func(x, L, A, x0, C):
    return L / (1 + np.exp((x - x0) / A)) + C


class LogisticFunctionFitter(LmfitBaseFitter):

    fit_params = [
        ["L", (1.0, 0.0, 1e10, True)],
        ["A", (1.0, 0.0, 1e10, True)],
        ["x0", (1.0, 0.0, 1e10, True)],
        ["C", (1.0, 0.0, 1e10, True)],
    ]

    name = "logistic_function"

    def func(self, x, L, A, x0, C):
        return logistic_func(x, L, A, x0, C)

    def add_derived_result_quantities(self):
        self.derived_results.New("max_slope", float, initial=10)

    def process_results(self, fit_results):
        L, A, x0, C = fit_results
        self.derived_results["max_slope"] = -L / (4 * A)
        return fit_results
