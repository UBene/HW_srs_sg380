'''
Created on Apr 4, 2022

@author: Benedikt Ursprung
'''
import numpy as np

ContrastModes = ['signalOverReference', 'differenceOverSum', 'signalOnly']


def calculateContrast(contrastMode, signal, background):
    # Calculates contrast based on the user's chosen contrast mode (configured in the experiment config file e.g. ESRconfig, Rabiconfig, etc)
    if contrastMode == "signalOverReference":
        return np.divide(signal, background)
    elif contrastMode == "differenceOverSum":
        return np.divide(
            np.subtract(signal, background), np.add(signal, background)
        )
    elif contrastMode == "signalOnly":
        return signal