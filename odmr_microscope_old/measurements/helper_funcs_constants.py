'''
Created on Mar 21, 2022

@author: bened
'''

import numpy as np
ContrastModes = ['ratio_SignalOverReference', 'ratio_DifferenceOverSum', 'signalOnly']

def calculateContrast(contrastMode, signal, background):
    # Calculates contrast based on the user's chosen contrast mode (configured in the experiment config file e.g. ESRconfig, Rabiconfig, etc)
    if contrastMode == "ratio_SignalOverReference":
        contrast = np.divide(signal, background)
    elif contrastMode == "ratio_DifferenceOverSum":
        contrast = np.divide(
            np.subtract(signal, background), np.add(signal, background)
        )
    elif contrastMode == "signalOnly":
        contrast = signal
    return contrast