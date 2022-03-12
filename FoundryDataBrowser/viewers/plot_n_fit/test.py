'''
Created on Mar 9, 2022

@author: Benedikt Ursprung
'''
from qtpy import QtWidgets
import numpy as np
#from . import TauXFitter, PolyFitter, SemiLogYPolyFitter,\
#                    MonoExponentialFitter, BiExponentialFitter, PeakUtilsFitter, PlotNFit

from FoundryDataBrowser.viewers.plot_n_fit.fitters.rate_equation import RateEquationFitter
from FoundryDataBrowser.viewers.plot_n_fit.plot_n_fit import PlotNFit

def main():
    app = QtWidgets.QApplication([])

    W = PlotNFit(fitters=[
        #BiExponentialFitter(),
        #MonoExponentialFitter(),
        #TauXFitter(),
        #PolyFitter(),
        #SemiLogYPolyFitter(),
        #PeakUtilsFitter(),
        RateEquationFitter()
    ])

    app.setActiveWindow(W.ui)
    W.ui.show()

    # Test latest fitter:
    x = np.arange(1200) / 12
    y = np.exp(-x / 8.0) + 0.01 * np.random.rand(len(x))
    # y = x - 10 + 0.001 * np.random.rand(len(x))

    W.update_data(x, y, 0)

    # x, y, = x[10:1100], y[10:1100]
    # W.update_fit_data(x, y)

    # hyperspec = np.array([y, y * 2, y * 3, y * 4, y * 5, y * 6]).reshape((3, 2, len(x)))

    # print(W.fit_hyperspec(x, hyperspec, -1))

    import sys
    sys.exit(app.exec())    


if __name__ == '__main__':
    main()
