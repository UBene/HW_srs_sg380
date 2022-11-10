# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from ScopeFoundry import BaseMicroscopeApp


class Microscope1App(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses
    # when storing data
    name = 'Schuck Group Microscope1'

    # You must define a setup function that adds all the
    #capablities of the microscope and sets default settings
    def setup(self):

        #Add App wide settings

        #Add hardware components
        print("Adding Hardware Components")

        from cnc_microscope.ScopeFoundryHW_CNC.powerwheel_arduino.power_wheel_main_arduino_hw import PowerWheelMainArduinoHW
        self.add_hardware(PowerWheelMainArduinoHW(self))

        from cnc_microscope.ScopeFoundryHW_CNC.powerwheel_arduino.power_wheel_side_arduino_hw import PowerWheelSideArduinoHW
        self.add_hardware(PowerWheelSideArduinoHW(self))

        # from ScopeFoundryHW_CNC.thorlabs_powermeter_Ge import ThorlabsPowerMeterGeHW
        # self.add_hardware(ThorlabsPowerMeterGeHW(self))
        #
        # from ScopeFoundryHW_CNC.thorlabs_powermeter_Si import ThorlabsPowerMeterSiHW
        # self.add_hardware(ThorlabsPowerMeterSiHW(self))
        from ScopeFoundryHW.thorlabs_powermeter.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware(ThorlabsPowerMeterHW(self, name = 'thorlabs_powermeter_Ge'))
        self.add_hardware(ThorlabsPowerMeterHW(self, name = 'thorlabs_powermeter_Si'))

        from cnc_microscope.ScopeFoundryHW_CNC.chameleon_ultra_ii_laser_hardware import ChameleonUltraIILaserHW
        self.add_hardware(ChameleonUltraIILaserHW(self))

        from cnc_microscope.ScopeFoundryHW_CNC.chameleon_opo_vis_hardware import ChameleonOPOVisHW
        self.add_hardware(ChameleonOPOVisHW(self))

        from ScopeFoundryHW.lightfield.lightfield_hw import LightFieldHW
        self.add_hardware(LightFieldHW(self))

        # self.add_hardware(PicamHW("lightfield"))

        from ScopeFoundryHW.lightfield.lightfield_hw_IR import LightFieldHW_IR
        self.add_hardware(LightFieldHW_IR(self))

        #from ScopeFoundryHW.oceanoptics_spec import OceanOpticsSpectrometerHW
        #self.add_hardware(OceanOpticsSpectrometerHW(self))

        # from ScopeFoundryHW_CNC.apd_counter_usb import APDCounterUSBHW
        # self.add_hardware(APDCounterUSBHW(self))

        

        #from ScopeFoundryHW.apd_counter_hydraharp import APDCounterHHarpHW
        #self.add_hardware(APDCounterHHarpHW(self))

        from cnc_microscope.ScopeFoundryHW_CNC.hydraharp import HydraHarpHW
        self.add_hardware(HydraHarpHW(self))

        from cnc_microscope.ScopeFoundryHW_CNC.PI_xyz_stage import PIXYZStageHW
        self.add_hardware(PIXYZStageHW(self))

        from cnc_microscope.ScopeFoundryHW_CNC.dual_position_slider_hw import DualPositionSliderHW
        self.add_hardware(DualPositionSliderHW(self))

        from cnc_microscope.ScopeFoundryHW_CNC.dual_position_slider_hw_2 import DualPositionSliderHW

        self.add_hardware(DualPositionSliderHW(self))

        #from ScopeFoundryHW.keithley_sourcemeter_hw import KeithleySourceMeterComponent
        #self.add_hardware( KeithleySourceMeterComponent(self) )

        #from ScopeFoundryHW.photodiode_adc import PhotodiodeADCHW
        #self.add_hardware(PhotodiodeADCHW(self))
        from cnc_microscope.ScopeFoundryHW_CNC.MotorizedRotationStageK10CR1_Excitation_HW import MotorizedStage_Excitation_HW
        self.add_hardware(MotorizedStage_Excitation_HW(self))
        
        from cnc_microscope.ScopeFoundryHW_CNC.MotorizedRotationStageK10CR1_Collection_HW import MotorizedStage_Collection_HW
        self.add_hardware(MotorizedStage_Collection_HW(self))

        # from ScopeFoundryHW.toupcam.toupcam_hw import ToupCamHW
        # self.add_hardware(ToupCamHW(self))





        #Add measurement components
        print("Create Measurement objects")

        from cnc_microscope.ScopeFoundryMeasurement.powermeter_optimizer_Ge import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))
        
        from cnc_microscope.ScopeFoundryMeasurement.powermeter_optimizer_Si_autozero import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))


        #from ScopeFoundryMeasurement.oo_spec_measure import OOSpecLive
        #self.add_measurement(OOSpecLive(self))    
        
        # from ScopeFoundryMeasurement.apd_optimizer import APDOptimizerMeasure
        # self.add_measurement(APDOptimizerMeasure(self))   
        #

        #from ScopeFoundryMeasurement.power_scan import PowerScanMeasure
        #self.add_measurement(PowerScanMeasure(self))    
        
        from cnc_microscope.ScopeFoundryMeasurement.power_scan_for_Ge_Si_2 import PowerScanMeasure_2pm
        self.add_measurement(PowerScanMeasure_2pm(self))
        
        #from ScopeFoundryMeasurement.power_scan_lifetime_new import PowerScanMeasure_lifetime
        #self.add_measurement(PowerScanMeasure_lifetime(self))
        
        #from ScopeFoundryMeasurement.power_scan_transmission import PowerScanTran
        #self.add_measurement(PowerScanTran(self))
        
        #from ScopeFoundryMeasurement.hydraharp_hist_measure import HydraHarpHistogramMeasure
        #self.add_measurement(HydraHarpHistogramMeasure(self))    
        
        #from ScopeFoundryMeasurement.base_3d_scan import PIStage3DStackSlowScan
        #self.add_measurement(PIStage3DStackSlowScan(self))   
        
        #from ScopeFoundryMeasurement.base_3d_scan import PIStage2DFrameSlowScan
        #self.add_measurement(PIStage2DFrameSlowScan(self))  
        
        from cnc_microscope.ScopeFoundryMeasurement.base_3d_scan import PI_2DScan
        self.add_measurement(PI_2DScan(self))

        #from ScopeFoundryMeasurement.base_3d_scan import PI_2DScan
        #self.add_measurement(PI_2DScan(self))
        
        
        from cnc_microscope.ScopeFoundryMeasurement.lightfield_readout import LightFieldReadout
        self.add_measurement(LightFieldReadout(self)) 
        
        from cnc_microscope.ScopeFoundryMeasurement.lightfield_readout_image import LightFieldImageReadout
        self.add_measurement(LightFieldImageReadout(self)) 

        from cnc_microscope.ScopeFoundryMeasurement.lightfield_readout_IR import LightFieldReadout_IR
        self.add_measurement(LightFieldReadout_IR(self))

        from cnc_microscope.ScopeFoundryMeasurement.chameleon_ple import ChameleonPLEMeasure
        self.add_measurement(ChameleonPLEMeasure(self))
        
        #from ScopeFoundryMeasurement.power_scan_map import PowerScanMap2D
        #self.add_measurement(PowerScanMap2D(self))
        
        #from ScopeFoundryMeasurement.power_scan_map_lifetime import PowerScanMap2D_lifetime
        #self.add_measurement(PowerScanMap2D_lifetime(self))
        
        #from ScopeFoundryMeasurement.chameleon_photoconductivity import ChameleonPhotoconductivityMeasure
        #self.add_measurement(ChameleonPhotoconductivityMeasure(self))
        
        #from ScopeFoundryMeasurement.power_trace_on_off_pmpower import PowerTrace_OnOff
        #self.add_measurement(PowerTrace_OnOff(self))
        
        from cnc_microscope.ScopeFoundryMeasurement.PolarizationScan import PolarizationScanMeasure
        self.add_measurement(PolarizationScanMeasure(self))

        from cnc_microscope.ScopeFoundryMeasurement.CNC_ver_3 import CNC
        self.add_measurement(CNC(self))

        #from ScopeFoundryMeasurement.CNC_ver3 import CNC
        #self.add_measurement(CNC(self))

        #from ScopeFoundryMeasurement.CNC_test import CNC
        #self.add_measurement(CNC(self))

        # from ScopeFoundryMeasurement.tiled_large_area_map import PIToupcamTiledLargeAreaMapMeasure
        # self.add_measurement(PIToupcamTiledLargeAreaMapMeasure(self))

        # from ScopeFoundryHW.toupcam.toupcam_spot_optimizer_ver_2 import ToupCamSpotOptimizer
        # self.add_measurement(ToupCamSpotOptimizer(self))

        # APD
        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement(APDOptimizerCBMeasurement(self))
        # from confocal_measure.pi_xyz_scans.pi_xyz_2d_apd_slow_scan import PIXYZ2DAPDSlowScan
        # self.add_measurement(PIXYZ2DAPDSlowScan(self, **stage_inits))

        # picam
        # from ScopeFoundryHW.picam.picam_hw import PicamHW
        # self.add_hardware(PicamHW(self))
        # from ScopeFoundryHW.picam import PicamReadoutMeasure
        # self.add_measurement(PicamReadoutMeasure(self))
        # from confocal_measure.pi_xyz_scans.pi_xyz_2d_picam_slow_scan import PIXYZ2DPICAMSlowScan
        # self.add_measurement(PIXYZ2DPICAMSlowScan(self, **stage_inits))


        from ScopeFoundryHW.nidaqmx.galvo_mirrors.galvo_mirrors_hw import GalvoMirrorsHW
        self.add_hardware(GalvoMirrorsHW(self))



        self.ui.show()
        self.ui.activateWindow()



if __name__ == '__main__':
    import sys
    print('test')
    #print(sys.argv)
    #print(1)
    app = Microscope1App(sys.argv)
    app.settings_load_ini('defaults.ini')
    sys.exit(app.exec_())