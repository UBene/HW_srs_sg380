"""
Created on Mar 9, 2022

@author: Benedikt Ursprung
"""
import numpy as np
from lmfit import Model, Parameter, Parameters, report_fit
from scipy import integrate, optimize
from FoundryDataBrowser.viewers.plot_n_fit.fitters.base_fitter import BaseFitter
from FoundryDataBrowser.viewers.plot_n_fit.helper_functions import dict2htmltable


def power2flux(power, wls=1064e-9):
    print(wls)
    Eph = 6.626e-34 * 2.998e8 / wls
    return power / Eph


def power2power_density(power, wls=1064e-9, NA=1):
    A = np.pi * (wls / (2 * NA) / 2) ** 2
    return power / A


def RHS(n3, args):
    """
    model equation from SI of https://doi.org/10.1038/s41586-020-03092-9
    returns RHS of Eqn S.2 as a function of n3 (assuming dn1/dt = 0)
    
    args:
    flux : # / area
    recombination parameters : [Frequency]    
    """
    # params
    flux, acs_12, acs_23, s_31, w2, w3_r, w3_nr, Q_22, Q_23, b_32 = args

    # Solving Eqn S.1 for n2 as a function of n3 (used Eqn S.3 to eliminate n1
    # and dn1/dt = 0)
    a = Q_23
    b = s_31 * n3 + acs_23 * flux
    c = -(s_31 * (1.0 - n3) * n3 + (w3_r + w3_nr) * n3)
    n2 = (-b + (b ** 2.0 - 4.0 * a * c) ** 0.5) / (2.0 * a)

    # solve for n1 using Eqn S.3
    n1 = 1.0 - n2 - n3

    # Eqn S.2 + Eqn S.1
    dn2_dt = (
        -acs_12 * flux * n1
        + w2 * n2
        + (1.0 - b_32) * (w3_r + w3_nr) * n3
        - s_31 * n1 * n3
        + (Q_22 + Q_23) * n2 ** 2
    )

    return dn2_dt


def fit_function(
    power_densities,
    acs_12,
    acs_23,
    s_31,
    w2,
    w3_r,
    w3_nr,
    Q_22,
    Q_23,
    b_32,
    scale,
    wls,
    use_gaussian_beam_correction,
):
    """
    power_densities  [power/area]
    scale, b_32 [-]
    all other [1/time]
    """
    print("fit_function", power_densities, acs_12, wls)
    power_densities = np.array([power_densities.min() / 1e5, *power_densities])
    fluxes = power2flux(power_densities, wls)
    n3 = np.zeros_like(fluxes)
    for i, flux in enumerate(fluxes):
        args = [flux, acs_12, acs_23, s_31, w2, w3_r, w3_nr, Q_22, Q_23, b_32]
        n3[i] = optimize.brentq(RHS, 0, 1, args=args)

    if use_gaussian_beam_correction:
        # Gaussian Beam Correction see 10.1103/PhysRevB.55.8240
        # fluorescence averaged over a gaussian beam with peak flux density flux_i
        _flourescences = integrate.cumulative_trapezoid(
            n3 / fluxes, x=fluxes, initial=0
        )
    else:
        # With no Beam correction the measured flouresence is proportional to n3
        _flourescences = n3

    return scale * _flourescences[1:]  # measured flouresence


class RateEquationFitter(BaseFitter):

    fit_params = [
        ["acs_12", (6.0000e-29, 0.0, 1e30, False)],
        ["acs_23", (6.4000e-25, 0.0, 1e30, False)],
        ["s_31", (10240.0000, 0.0, 1e30, False)],
        ["w2", (219.500000, 0.0, 1e30, True)],
        ["w3_r", (636.010000, 0.0, 1e30, False)],
        ["w3_nr", (103.580000, 0.0, 1e30, False)],
        ["Q_22", (158.894411, 0.0, 1e30, False)],
        ["Q_23", (55.8613165, 0.0, 1e30, False)],
        ["b_32", (0.14400000, 0.0, 1e30, False)],
        ["scale", (20.0000000, 0.0, 1e30, True)],
        ["wls", (1.0640e-06, 0.0, 1e30, False)],
        ["use_gaussian_beam_correction", (0.0, 0.0, 1e30, False)],
    ]
    name = "rate_equation"

    def fit_xy(self, x: np.array, y: np.array) -> np.array:
        model = Model(fit_function, independent_vars=["power_densities"])
        params = model.make_params()
        for p in params:
            params[p].value = self.initials[p]
            params[p].init_value = self.initials[p]
            params[p].min = self.bounds[p + "_lower"]
            params[p].max = self.bounds[p + "_upper"]
            params[p].vary = self.vary[p]
        res = model.fit(y, params, power_densities=x)
        fit = fit_function(x, **res.values)

        self.set_result_message(res.message + dict2htmltable(res.values))
        return fit
