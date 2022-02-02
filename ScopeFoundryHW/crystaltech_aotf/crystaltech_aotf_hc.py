        # Frequency property
        # TODO:  only works on channel 0!
        
        # Power property
        # TODO:  only works on channel 0!
import numpy as np

from ScopeFoundry import HardwareComponent
try:
    from ScopeFoundryHW.crystaltech_aotf.crystaltech_dds import CrystalTechDDS
except Exception as err:
    print("Cannot load required modules for CrystalTech DDS (AOTF):", err)

class CrystalTechAOTF(HardwareComponent):
    
    name = 'CrystalTechAOTF_DDS'
        
    def setup(self):

        self.settings.New('port', str, initial='COM24')
                
        self.settings.New('modulation_enable',
                          dtype=bool,
                          ro=False)
        self.freq0 = self.settings.New('freq0',
                          dtype=float,
                          unit='MHz',
                          vmin=0,
                          vmax=200,
                          si=False,
                          fmt='%f')

        self.settings.New('pwr0',
                          dtype=int,
                          vmin=0,
                          vmax=1<<16,
                          si=False)
        
        self.deflected_wl  = self.settings.New('deflected_wl', dtype=float, unit='nm')
                
        #connect GUI
        """
        self.modulation_enable.connect_bidir_to_widget(self.gui.ui.aotf_mod_enable_checkBox)
        self.freq0.connect_bidir_to_widget(self.gui.ui.atof_freq_doubleSpinBox)
#        self.ui.aotf_freq_set_lineEdit.returnPressed.connect(self.aotf_freq.update_value)
        self.pwr0.connect_bidir_to_widget(self.gui.ui.aotf_power_doubleSpinBox)
#        self.ui.aotf_power_doubleSpinBox.valueChanged.connect(self.aotf_power.update_value)
        """
       
    def connect(self):

        #connect to hardware
        if self.debug_mode.val:print('Connecting...', self.name)   
        self.dds = CrystalTechDDS(comm="serial", port=self.settings['port'], debug=self.debug_mode.val)
        if self.debug_mode.val:print('Complete')
        
        # Connect logged quantities to hardware
        self.settings.modulation_enable.connect_to_hardware(
            write_func=self.dds.set_modulation)
        
        self.settings.freq0.connect_to_hardware(
            read_func=self.dds.get_frequency,
            write_func=self.dds.set_frequency)
        
        self.settings.pwr0.connect_to_hardware(
            read_func=self.dds.get_amplitude,
            write_func=self.dds.set_amplitude)

        self.load_calibration_data()
        self.deflected_wl.connect_lq_math(self.freq0, self.aotffreq2wls, reverse_func=self.wls2atoffreq)


    def disconnect(self):
        self.log.info('disconnect ' + self.name)
        
        #disconnect logged quantities from hardware
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'dds'):
            self.dds.close()
            del self.dds
            
    def load_calibration_data(self, calibration_fname='crystaltech_aotf_calibration.txt'):
        '''
        loads calibration data from 'calibration_fname' .txt-file located in this folder
        '''
        path = '../ScopeFoundryHW/crystaltech_aotf/'
        self.calib_aotf_freqs, self.calib_deflected_wls = np.loadtxt(path + calibration_fname).T
        self.deflected_wl.change_min_max(self.calib_deflected_wls.min(), self.calib_deflected_wls.max())
        #self.freq0.change_min_max(self.calib_aotf_freqs.min(), self.calib_aotf_freqs.max()) #may go further than calibrated?

    def wls2atoffreq(self, wl):
        argsort = np.argsort(self.calib_deflected_wls)
        return np.interp(x=wl, xp=self.calib_deflected_wls[argsort], fp=self.calib_aotf_freqs[argsort])
        
    def aotffreq2wls(self, freq):
        argsort = np.argsort(self.calib_aotf_freqs)
        return np.interp(x=freq, xp=self.calib_aotf_freqs[argsort], fp=self.calib_deflected_wls[argsort])