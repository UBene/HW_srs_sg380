# contrast function
# Copyright (c) 2018 Diana Prado Lopes Aude Craik
# Copyright (c) 2022 Benedikt Ursprung
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from enum import Enum

import numpy as np


class ContrastModes(Enum):
    signal_over_reference = 'signal_over_reference',
    fractional_difference_over_reference = 'fractional_difference_over_reference',
    difference_over_sum = 'difference_over_sum',
    signal_only = 'signal_only'
contrast_modes = tuple([(x.value, x.value) for x in ContrastModes])

def calculate_contrast(contrast_mode: str, signal: np.ndarray, background: np.ndarray) -> np.ndarray:
    if contrast_mode == ContrastModes.signal_over_reference.value:
        return np.divide(signal, background)
    if contrast_mode == ContrastModes.fractional_difference_over_reference.value:
        return 1.0 - np.divide(
            np.subtract(background, signal), background
        )
    if contrast_mode == ContrastModes.difference_over_sum.value:
        return np.divide(
            np.subtract(signal, background), np.add(signal, background)
        )
    if contrast_mode == ContrastModes.signal_only.value:
        return signal
