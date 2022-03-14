"""
Created on Mar 9, 2022

@author: Benedikt Ursprung
"""
import numpy as np
from .base_fitter import BaseFitter
from ..helper_functions import table2html


class TauXFitter(BaseFitter):

    fit_params = [["tau_x", None]]

    name = "tau_x"

    def fit_xy(self, x, y):

        t = x - x.min()

        tau = tau_x_calc(y - y[-3:].mean(), t)

        """
        there is an inaccuracy from integrating over a finite time interval rather than
        to infinity. 
        """
        decay_pct = (
            1 - y[-3:].mean() ** 2 / y[0:3].mean() ** 2
        ) * 100  # should be 100%
        inaccuracy_pct = (1 - np.exp(-tau / t.max())) * 100  # should be 0

        msg1 = f"decay level: {decay_pct:0.1f}%".rjust(100)
        msg2 = f"normalization inaccuracy: {inaccuracy_pct:0.1f}%".rjust(100)
        self.update_fit_results([tau], msg1 + "<br>" + msg2)

        # Error from not integrating over

        if tau == 0:  # handle wierd case so it doesn't crash
            return np.ones_like(y)
        return y[0:3].mean() * np.exp(-t / tau)

    def fit_hyperspec(self, x, _hyperspec, axis=-1):
        return tau_x_calc_map(x, _hyperspec, axis=axis)

    def hyperspec_descriptions(self):
        return ["tau_x"]


def tau_x_calc(time_trace, time_array, X=0.6321205588300001):
    f = time_trace
    return time_array[np.argmin((np.cumsum(f) / np.sum(f) - X) ** 2)]


def tau_x_calc_map(time_array, time_trace_map, X=0.6321205588300001, axis=-1):
    kwargs = dict(time_array=time_array, X=X)
    return np.apply_along_axis(tau_x_calc, axis=axis, arr=time_trace_map, **kwargs)


class PeakUtilsFitter(BaseFitter):

    name = "peakUtils"

    def add_settings_quantities(self):
        self.settings.New("baseline_deg", int, initial=0, vmin=-1, vmax=100)
        self.settings.New("thres", float, initial=0.5, vmin=0, vmax=1)
        self.settings.New("unique_solution", bool, initial=False)
        self.settings.New("min_dist", int, initial=-1)
        self.settings.New("gaus_fit_refinement", bool, initial=True)
        self.settings.New("ignore_phony_refinements", bool, initial=True)

    def fit_xy(self, x, y):

        PS = self.settings
        import peakutils

        base = 1.0 * peakutils.baseline(y, PS["baseline_deg"])

        if PS["min_dist"] < 0:
            min_dist = int(len(x) / 2)
        else:
            min_dist = PS["min_dist"]
        peaks_ = peaks(
            y - base,
            x,
            PS["thres"],
            PS["unique_solution"],
            min_dist,
            PS["gaus_fit_refinement"],
            PS["ignore_phony_refinements"],
        )

        peaks_ = np.atleast_1d(peaks_)
        self.highlight_x_vals = peaks_

        res_table = []
        header = ["peaks"]
        for i, p in enumerate(peaks_):
            res_table.append(["{:3.3f}".format(p)])
        html_table = table2html(res_table, header)
        self.set_result_message(html_table)

        # have to return something of len(x) to plot
        return base

    def fit_hyperspec(self, x, _hyperspec, axis=-1):
        PS = self.settings
        return peak_map(
            _hyperspec,
            x,
            axis,
            PS["thres"],
            int(len(x) / 2),
            PS["gaus_fit_refinement"],
            PS["ignore_phony_refinements"],
        )

    def hyperspec_descriptions(self):
        return ["peak"]

    def state_description(self):
        s = ""
        if self.settings["gaus_fit_refinement"]:
            s += "_refined"
            if self.settings["ignore_phony_refinements"]:
                s += "_ignored"
        return s


def peaks(
    spec,
    wls,
    thres=0.5,
    unique_solution=True,
    min_dist=-1,
    refinement=True,
    ignore_phony_refinements=True,
):
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
                        "peakutils.interpolate() yielded result outside wls range, returning unrefined result"
                    )
                    peaks_x[i] = wls[indexes[i]]
    else:
        peaks_x = wls[indexes]

    if unique_solution:
        return peaks_x[0]
    else:
        return peaks_x


def peak_map(
    hyperspectral_data, wls, axis, thres, min_dist, refinement, ignore_phony_refinements
):
    return np.apply_along_axis(
        peaks,
        axis,
        hyperspectral_data,
        wls=wls,
        thres=thres,
        unique_solution=True,
        min_dist=min_dist,
        refinement=refinement,
        ignore_phony_refinements=ignore_phony_refinements,
    )
