"""
Created on Mar 9, 2022

@author: Benedikt Ursprung
"""
from qtpy import QtWidgets
import numpy as np


from FoundryDataBrowser.viewers.plot_n_fit import PlotNFit
from FoundryDataBrowser.viewers.plot_n_fit import (
    LogisticFunctionFitter,
    MonoExponentialFitter,
    BiExponentialFitter,
    RateEquationFitter,
    TauXFitter,
    PeakUtilsFitter,
    SemiLogYPolyFitter,
    PolyFitter,
)


def test_logistic_func(W):
    x = np.linspace(-10, 10, 50)
    from FoundryDataBrowser.viewers.plot_n_fit.fitters.lmfit import logistic_func

    L, A, x0, C = 11, 1, 0.5, 2.1
    params = [L, A, x0, C]
    y = logistic_func(x, *params)
    y += 0.01 * L * np.random.rand(len(x))
    W.update_data(x, y, 0)
    return x, y


def test_mono_exponential_funcs(W):
    x = np.arange(1200) / 12
    y = np.exp(-x / 8.0) + 0.01 * np.random.rand(len(x))
    W.update_data(x, y, 0)
    return x, y


def test_hyperspec(W, x, y):
    hyperspec = np.array([y, y * 2, y * 3, y * 4, y * 5, y * 6]).reshape((3, 2, len(x)))
    print(W.fit_hyperspec(x, hyperspec, -1))


def main():
    app = QtWidgets.QApplication([])

    W = PlotNFit(
        fitters=[
            BiExponentialFitter(),
            MonoExponentialFitter(),
            TauXFitter(),
            PolyFitter(),
            SemiLogYPolyFitter(),
            PeakUtilsFitter(),
            # RateEquationFitter(),
            LogisticFunctionFitter(),
        ]
    )

    app.setActiveWindow(W.ui)
    W.ui.show()

    # x, y = test_mono_exponential_funcs(W)
    x, y = test_logistic_func(W)

    # test_hyperspec(W, x, y)

    import sys

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
