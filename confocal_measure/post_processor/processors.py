'''
Created on Mar 6, 2022

@author: Benedikt Ursprung
'''

import numpy as np


def gauss(x, a, x0, sigma):
    return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

    
def fit_gauss(x, y):
    from scipy.optimize import curve_fit
    p0 = [y.max(), x[y.argmax()], 10]
    popt, _ = curve_fit(gauss, x, y, p0=p0)
    return popt  # a,mean,sigma 


def post_process_gauss(z, f):
    a, mean, sigma = fit_gauss(z, f - f.min())
    f0 = gauss(z, a, mean, sigma) + f.min()
    z0 = mean     
    return z0, f0

    
def post_process_min(z, f):
    return z[np.array(f.argmin())], f


def post_process_max(z, f):
    return z[np.array(f.argmax())], f
    

post_processors = {'gauss_mean':post_process_gauss,
                   'min': post_process_min,
                   'max': post_process_max}
