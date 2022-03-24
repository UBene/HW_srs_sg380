"""
Created on Mar 14, 2022

@author: Benedikt Ursprung
"""
import numpy as np
from .base_fitter import BaseFitter
from ..helper_functions import table2html


class PolyFitter(BaseFitter):

    name = "poly"

    def add_settings_quantities(self):
        self.settings.New("deg", int, initial=1)

    def transform(self, x, y):
        return x, y

    def inverse_transform(self, x, y):
        return x, y

    def fit_xy(self, x, y):
        deg = self.settings["deg"]

        x_, y_ = self.transform(x, y)

        coefs = np.polynomial.polynomial.polyfit(x_, y_, deg)
        fit_ = np.polynomial.polynomial.polyval(x_, coefs)
        x, fit = self.inverse_transform(x, fit_)

        res_table = []
        header = ["coef", "value"]
        for i, c in enumerate(coefs):
            res_table.append([f"a{i}", "{:3.3f}".format(c)])

        html_table = table2html(res_table, header)
        self.set_result_message(html_table)

        return fit

    def fit_hyperspec(self, x, _hyperspec, axis=-1):

        x_, h_ = self.transform(x, _hyperspec)

        # polyfit takes 2D array and fits along dim 0.
        h_ = h_.swapaxes(axis, 0)
        shape = h_.shape[1:]
        h_ = h_.reshape((len(x), -1))

        deg = self.settings["deg"]
        coefs = np.polynomial.polynomial.polyfit(x_, h_, deg)
        Res = coefs.reshape(-1, *shape).swapaxes(0, axis)
        return Res

    def hyperspec_descriptions(self):
        return [f"a{i}" for i in range(self.settings["deg"])]


class SemiLogYPolyFitter(PolyFitter):

    name = "semilogy_poly"

    def transform(self, x, y):
        return x, np.log(y)

    def inverse_transform(self, x, y):
        return x, np.exp(y)


class LogLogPolyFitter(PolyFitter):

    name = "loglog"

    def transform(self, x, y):
        return np.log10(x), np.log10(y)

    def inverse_transform(self, x, y):
        return 10 ** x, 10 ** y
