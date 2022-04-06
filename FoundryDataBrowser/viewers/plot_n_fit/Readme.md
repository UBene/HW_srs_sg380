## Usage

```python
from plot_n_fit import PlotNFit, BiExponentialFitter, LogisticFunctionFitter

W = PlotNFit(
        fitters=[
            BiExponentialFitter(),
            LogisticFunctionFitter(),
        ]
W.update_data(x, y)
```



## New fitter

See `ScopeFoundry/widgets/lmfit_fitters` if you need to want to dynamically change witch parameters to vary. Otherwise `ScopeFoundry/widgets/least_squares_fitters` 



## Requires

`Scopefoundry`

`DataSelector` class in`ScopeFoundry.widgets `

Some fitters require

`scipy` and or `lmfit`