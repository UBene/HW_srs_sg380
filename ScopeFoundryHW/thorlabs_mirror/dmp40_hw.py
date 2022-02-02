'''
Created on Aug 22, 2017

@author: Alan Buckley <alanbuckley@lbl.gov>
                        <alanbuckley@berkeley.edu>
'''

from ScopeFoundry import HardwareComponent
from operator import itemgetter
from collections import OrderedDict
from ScopeFoundryHW.thorlabs_mirror.dmp40_dev import ThorlabsDMP40
import ctypes
import numpy as np

class ThorlabsDMP40_HW(HardwareComponent):
    
    name = "dmp40_hw"
    
    zernike = {
            'Z4_Astigmatism_45': 0x00000001,
            'Z5_Defocus': 0x00000002,
            'Z6_Astigmatism_0': 0x00000004,
            'Z7_Trefoil_Y': 0x00000008,
            'Z8_Coma_X': 0x00000010,
            'Z9_Coma_Y': 0x00000020,
            'Z10_Trefoil_X': 0x00000040,
            'Z11_Tetrafoil_Y': 0x00000080,
            'Z12_Sec_Astig_Y': 0x00000100,
            'Z13_3O_Sph_Abberation': 0x00000200,
            'Z14_Sec_Astig_X': 0x00000400,
            'Z15_Tetrafoil_X': 0x00000800}
    zernike_ordered = OrderedDict(sorted(zernike.items(), key=lambda t: t[0]))
    
    def setup(self):
        for k in self.zernike_ordered.keys():
            self.settings.New(name=k, dtype=float, initial=0.0, fmt="%.3f", vmin=-1.0, vmax=1.0, ro=False)

        self.settings.New(name="IC1_temp", dtype=float, initial=0.0, fmt="%.3f", vmin=0.0, vmax=50.0, ro=True)
        self.settings.New(name="IC2_temp", dtype=float, initial=0.0, fmt="%.3f", vmin=0.0, vmax=50.0, ro=True)
        self.settings.New(name="Mirror_temp", dtype=float, initial=0.0, fmt="%.3f", vmin=0.0, vmax=50.0, ro=True)
        self.settings.New(name="Electronics_temp", dtype=float, initial=0.0, fmt="%.3f", vmin=0.0, vmax=50.0, ro=True)
        

        self.add_operation(name="apply_Zernike_pattern", op_func=self.set_zernike_patterns)
        self.add_operation(name="relax", op_func=self.relax)
        self.add_operation(name="reset", op_func=self.reset)
                   
    def connect(self):
        self.dev = ThorlabsDMP40(debug=self.settings.debug_mode.val)
        

    def zernike_active_readout(self):
        self.read_from_hardware()
        selected = []
        for k, _ in self.zernike.items():
            if self.settings[k] != 0.0:
                if self.settings.debug_mode.val:
                    print(k)
                selected.append(k)
        return selected
    
    def relax(self):
        if self.dev:
            self.dev.relax()
        else:
            pass
    
    def reset(self):
        if self.dev:
            self.dev.reset()
        else:
            pass
    
    def calculate_zernike_integer(self):
        selected_zernikes = self.zernike_active_readout()
        if self.settings.debug_mode.val:
            print(selected_zernikes, self.zernike)
            print(itemgetter(*selected_zernikes))
        zernike_integers = itemgetter(*selected_zernikes)(self.zernike)
        if isinstance(zernike_integers, int):
            return zernike_integers
        else:
            return sum(zernike_integers)
        
    def set_zernike_patterns(self):
        amplitudes = []
        for k in self.zernike.keys():
            amplitudes.append(self.settings[k])
        np_ampl = np.asarray(amplitudes)
        ct_ampl = self.dev.np64_to_ctypes64(np_ampl)
        mirror_pattern = (ctypes.c_double * 40)()
        zern_int = self.calculate_zernike_integer()
        self.dev.dll_ext.TLDFMX_calculate_zernike_pattern(self.dev.instHandle, 
                                                          ctypes.c_uint32(zern_int), ct_ampl, 
                                                          ctypes.byref(mirror_pattern))
        self.dev.set_segment_voltages(np.frombuffer(mirror_pattern)) 
    
    def disconnect(self):
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'dev'):
            self.dev.close()
            del self.dev
        