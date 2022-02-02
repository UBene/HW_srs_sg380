from __future__ import division, print_function
from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level='DEBUG')  # , filename='m3_log.txt')
# logging.getLogger('').setLevel(logging.WARNING)
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class NearFieldMicroscope(BaseMicroscopeApp):

    name = 'near_field_microscope'

    def setup(self):

        print("Adding Hardware Components")

        #import ScopeFoundryHW.picoharp as ph
        #self.add_hardware(ph.PicoHarpHW(self))

        from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
        self.add_hardware(HydraHarpHW(self))

        #from ScopeFoundryHW.winspec_remote import WinSpecRemoteClientHW
        #self.add_hardware_component(WinSpecRemoteClientHW(self))

        #from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        #self.add_hardware(ActonSpectrometerHW(self))

        # from ScopeFoundryHW.tenma_power.tenma_hw import TenmaHW
        # self.add_hardware(TenmaHW(self))

        #from ScopeFoundryHW.pololu_servo.multi_servo_hw import PololuMaestroHW, PololuMaestroWheelServoHW, PololuMaestroShutterServoHW
        #self.add_hardware(PololuMaestroHW(self, name='pololu_maestro'))
        #self.add_hardware(PololuMaestroWheelServoHW(self, name='power_wheel', channel=0))

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))
        
        
        #from ScopeFoundryHW.thorlabs_stepper_motors import ThorlabsStepperControllerHW
        #self.add_hardware(ThorlabsStepperControllerHW(self))
        
        
        from ScopeFoundryHW.thorlabs_integrated_stepper.thorlabs_integrated_stepper_motor_hw import ThorlabsIntegratedStepperMottorHW
        self.add_hardware_component(ThorlabsIntegratedStepperMottorHW(self))
        

        # from ScopeFoundryHW.thorlabs_powermeter.thorlabs_powermeter_analog_readout import ThorlabsPowerMeterAnalogReadOut
        # self.add_hardware(ThorlabsPowerMeterAnalogReadOut(self))

        #from ScopeFoundryHW.dli_powerswitch import DLIPowerSwitchHW
        #dli = self.add_hardware(DLIPowerSwitchHW(self))

        #from ScopeFoundryHW.attocube_ecc100.attocube_xyz_hw import AttoCubeXYZStageHW
        #self.add_hardware(AttoCubeXYZStageHW(self))

        #from ScopeFoundryHW.powermate.powermate_hw import PowermateHW
        #self.add_hardware(PowermateHW(self))

        # from ScopeFoundryHW.thorlabs_motorized_filter_flipper.thorlabsMFF_hardware import ThorlabsMFFHW
        # self.add_hardware_component(ThorlabsMFFHW(self))

        # from ScopeFoundryHW.xbox_controller.xbox_controller_hw import XboxControllerHW
        # self.add_hardware(XboxControllerHW(self))

        #from ScopeFoundryHW.filter_wheel_arduino.filter_wheel_arduino_hw import FilterWheelArduinoHW
        #self.add_hardware(FilterWheelArduinoHW(self))

        # from ScopeFoundryHW.arduino_tc4.arduino_tc4_hw import ArduinoTc4HW
        # self.add_hardware(ArduinoTc4HW(self))

        #from ScopeFoundryHW.chameleon_compact_opo.chameleon_compact_opo_hw import ChameleonCompactOPOHW
        #self.add_hardware(ChameleonCompactOPOHW(self))

        # from ScopeFoundryHW.keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        # self.add_hardware(KeithleySourceMeterComponent(self))

        #from ScopeFoundryHW.andor_camera import AndorCCDHW, AndorCCDReadoutMeasure
        #self.add_hardware(AndorCCDHW(self))
        #self.add_measurement(AndorCCDReadoutMeasure)

        #from ScopeFoundryHW.toupcam.toupcam_hw import ToupCamHW
        #self.add_hardware(ToupCamHW(self))

        #from ScopeFoundryHW.thorlabs_elliptec.elliptec_hw import ThorlabsElliptecSingleHW
        #self.add_hardware(ThorlabsElliptecSingleHW(self, name='polarizer'))

        #from ScopeFoundryHW.lakeshore_331.lakeshore_hw import Lakeshore331HW
        #self.add_hardware(Lakeshore331HW(self))

        print("Adding Measurement Components")

        #from ir_microscope.measurements.hyperspectral_scan import AndorHyperSpec2DScan
        #self.add_measurement(AndorHyperSpec2DScan(self))

        # self.add_measurement(ph.PicoHarpChannelOptimizer(self))
        # self.add_measurement(ph.PicoHarpHistogramMeasure(self))
        # self.add_measurement(trpl_scan.TRPL2DScan(self, shutter_open_lq_path='hardware/shutter/open'))

        from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
        self.add_measurement(HydraHarpOptimizerMeasure(self))
        
        #from ir_microscope.measurements.trpl_scan import TRPL2DScan
        #self.add_measurement(TRPL2DScan(self))
        
        from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
        self.add_measurement(HydraHarpHistogramMeasure(self))

        #from ScopeFoundryHW.winspec_remote import WinSpecRemoteReadoutMeasure
        #self.add_measurement(WinSpecRemoteReadoutMeasure(self))

        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement(PowerScanMeasure(self, 
                                              #shutter_open_lq_path='hardware/shutter/open'
                                              )
        )

        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))

        #from ScopeFoundryHW.attocube_ecc100.attocube_stage_control import AttoCubeStageControlMeasure
        #self.add_measurement(AttoCubeStageControlMeasure(self))


        #self.add_measurement(PowermateMeasure(self, n_devs=3, dev_lq_choices=choices))

        # from ScopeFoundryHW.attocube_ecc100.attocube_home_axis_measurement import AttoCubeHomeAxisMeasurement
        # self.add_measurement(AttoCubeHomeAxisMeasurement(self))

        # from measurements.stage_motion_measure import StageHomeAxesMeasure
        # self.add_measurement(StageHomeAxesMeasure(self))

        # from measurements.xbox_controller_measure import XboxControllerMeasure
        # self.add_measurement(XboxControllerMeasure(self))

        # from measurements.laser_line_writer import LaserLineWriter
        # self.add_measurement(LaserLineWriter(self))

        #from ir_microscope.measurements.laser_power_feedback_control import LaserPowerFeedbackControl
        #self.add_measurement(LaserPowerFeedbackControl(self))

        # from ir_microscope.measurements.position_recipe_control import PositionRecipeControl
        # self.add_measurement(PositionRecipeControl(self))
        # from ir_microscope.measurements.focus_recipe_control import FocusRecipeControl
        # self.add_measurement(FocusRecipeControl(self))

        # from ir_microscope.measurements.apd_scan import PicoharpApdScan
        # self.add_measurement(PicoharpApdScan(self, use_external_range_sync=True))

        #from confocal_measure.calibration_sweep import CalibrationSweep
        #self.add_measurement(CalibrationSweep(self, spectrometer_hw_name='acton_spectrometer',
        #                                            camera_readout_measure_name='andor_ccd_readout'))

        #from ir_microscope.measurements.nested_measurements import NestedMeasurements
        #self.add_measurement(NestedMeasurements(self))

        # from ir_microscope.measurements.trpl_parallelogram_scan import TRPLParallelogramScan
        # self.add_measurement(TRPLParallelogramScan(self, use_external_range_sync=False))

        # from ScopeFoundryHW.keithley_sourcemeter.iv_base_measurement import IVBaseMeasurement,IVTRPL
        # self.add_measurement(IVBaseMeasurement(self))
        # self.add_measurement(IVTRPL(self))

        # from ScopeFoundryHW.crystaltech_aotf.crystaltech_aotf_hc import CrystalTechAOTF
        # self.add_hardware(CrystalTechAOTF(self))

        # from ScopeFoundryHW.xbox_controller.xbox_controller_test_measure import

        #from ir_microscope.measurements.live_cam import LiveCam
        #self.add_measurement(LiveCam(self))

        # from confocal_measure.toupcam_spot_optimizer import AttocubeToupCamLive
        # self.add_measurement(AttocubeToupCamLive)

        #from confocal_measure.toupcam_spot_optimizer import ToupCamSpotOptimizer
        #self.add_measurement(ToupCamSpotOptimizer(self))

        # from ir_microscope.measurements.live_cam import AttocubeToupcamRotationCalibration
        # self.add_measurement(AttocubeToupcamRotationCalibration)

        
        from confocal_measure.sequencer import Sequencer
        self.add_measurement(Sequencer(self))

        #from ScopeFoundryHW.dynamixel_servo import DynamixelXServosHW, DynamixelFilterWheelHW, DynamixelServoHW
        #self.add_hardware(DynamixelXServosHW(self, devices=dict(rotation_motor=42,)))
        #self.add_hardware(DynamixelServoHW(self, name='rotation_motor'))

        
        # connect mapping measurement settings
        #lq_names = ['h0', 'h1', 'v0', 'v1', 'Nh', 'Nv']

        #for scan in [apd_asi, hyperspec_asi, asi_trpl_2d_scan]:
        #    for lq_name in lq_names:
        #        master_scan_lq = apd_asi.settings.get_lq(lq_name)
        #        scan.settings.get_lq(lq_name).connect_to_lq(master_scan_lq)

        # from confocal_measure.x_dependence import XDependence
        # self.add_measurement(XDependence(self))
        
        
        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement_component(APDOptimizerCBMeasurement(self))  

        rainbow = '''qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 100), 
                        stop:0.166 rgba(255, 255, 0, 100), stop:0.333 rgba(0, 255, 0, 100), stop:0.5 rgba(0, 255, 255, 100), 
                        stop:0.666 rgba(0, 0, 255, 100), stop:0.833 rgba(255, 0, 255, 100), stop:1 rgba(255, 0, 0, 100))'''


        from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo_hw import DynamixelXServosHW
        from ScopeFoundryHW.dynamixel_servo.dynamixel_single_hw import DynamixelServoHW
        servos = self.add_hardware(DynamixelXServosHW(self, devices=dict(power_wheel=10,)))
        self.add_hardware(DynamixelServoHW(self, name='power_wheel'))        

        
        
    def setup_ui(self):
        self.add_quickbar(load_qt_ui_file('NearFieldMicroscope_quickbar.ui'))
        Q = self.quickbar
        S = self.hardware.power_wheel.settings
        S.position.connect_to_widget(Q.position_label)
        S.target_position.connect_to_widget(Q.target_position_doubleSpinBox)



if __name__ == '__main__':
    import sys
    app = NearFieldMicroscope(sys.argv)
    app.settings_load_ini('near_field_microscope_defaults.ini')
    app.load_window_positions_json(r'E:\Natalie\natalie_window_positions.json')
    sys.exit(app.exec_())