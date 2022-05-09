#!/usr/bin/env python
# coding: utf-8

# # configured power scans plot 
# 
# 
# designed to work with scopefoundry databrowser `power_scan_h5` viewer.
# 
# 1. In databrowser, 
#     click `commit_configs` for multiple files. First time operating in a folder hit `new notebook` to generate '.pynb'
# 2. Run the newely generated notebook (not this one if choose `new notebook`)
# 
# author: Benedikt Ursprung
# date: April 29th, 2022

# In[ ]:


import json
import matplotlib.pylab as plt
import numpy as np
from .power_scan_h5 import load_file


def get_dependence_data(power_array, spectra, signal_mask, background_mask, configs):
    channel = configs["channel"]
    binning = configs["power_binning"]
    conversion_factor = configs["conversion_factor"]

    if configs["bg_selector"]["activated"]:
        bg = spectra[:, channel, background_mask].mean()
    else:
        bg = 0

    data = spectra[:, channel, signal_mask]
    if binning > 1:
        Np, ns = data.shape
        data = (
            data[: (Np // binning) * binning, :].reshape(-1, binning, ns).mean(axis=1)
        )
    y = data.sum(axis=-1) - bg

    x = power_array
    if binning > 1:
        x = x[: (len(x) // binning) * binning].reshape(-1, binning).mean(-1)

    x = x * conversion_factor
    # only positive values
    mask = (y > 0) * (x > 0)
    return x[mask], y[mask]


def make_mask(configs, wls, selector="bg_selector"):
    N = len(wls)
    if configs[selector]["activated"]:

        if configs[selector]["mode"] == "mask":
            rgn = configs[selector]["region"]
            # print(selector,rgn, min(wls), max(wls), ((wls >= min(rgn)) * (wls <= max(rgn))).sum())
            return (wls >= min(rgn)) * (wls <= max(rgn))
        else:
            mask = np.zeros(N).astype(bool)
            s = slice(
                configs[selector]["start"],
                configs[selector]["stop"],
                configs[selector]["step"],
            )
            mask[s] = True
            return mask
    else:
        return np.ones(N, dtype=bool)


def configured_plot(config_file=None, target_dir=None):
    
    if target_dir is None:
        import os
        target_dir = os.getcwd()
        
    if config_file is None:
        import os
        config_file = os.getcwd() +  '/power_scans_configs'
    
    
    with open(config_file, "r") as f:
        configs_collection = json.load(f)
    
    
    slopes = []
    plt.figure()
    
    for fname, configs in configs_collection.items():
        if not configs["ignore"]:
            
            
            spectra, power_arrays, aquisition_type, sample, wls = load_file(f'{target_dir}/{fname}')
            power_array = power_arrays[configs["power_x_axis"]]
            x, y = get_dependence_data(
                power_array,
                spectra,
                make_mask(configs, wls, selector="signal_selector"),
                make_mask(configs, wls, selector="bg_selector"),
                configs,
            )
    
            # Fit
            power_mask = make_mask(configs["plot_n_fit"], x, selector="data_selector")
            x_, y_ = np.log10(x[power_mask]), np.log10(y[power_mask])
            coefs = np.polynomial.polynomial.polyfit(x_, y_, 1)
            fit = 10 ** np.polynomial.polynomial.polyval(x_, coefs)
            slopes.append(coefs[1])
    
            # plot
            plot_mask = make_mask(configs["plot_n_fit"], x, selector="plot_masker")
            p = plt.loglog(
                x[plot_mask],
                y[plot_mask],
                "x",
                label=f"{fname}  slope: {coefs[1]:1.2f} {sample} {configs['info']}",
            )
            # plt.loglog(
            #     x[power_mask],
            #     fit,
            #     "-",
            #     color=p[0].get_color(),
            #     label=f"slope: {coefs[1]:1.2f}",
            # )
            plt.loglog(x[power_mask], fit, "-", color="k")
    
    plt.xlabel("excitation power")
    plt.ylabel("emission")
    plt.savefig(
        f'{target_dir}/configured_power_scans.png',
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
    )
    plt.legend(bbox_to_anchor=(1.01, 1, 0.2, 0.0))
    plt.savefig(
        f'{target_dir}/configured_power_scans_w_legend.png',
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
    )
