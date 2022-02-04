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


class NikonMicroscope(BaseMicroscopeApp):

    name = 'nikon_microscope'

    def setup(self):

        print("Adding Hardware Components")

        from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
        self.add_hardware(HydraHarpHW(self))

        # from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        # self.add_hardware(ActonSpectrometerHW(self))

        from ScopeFoundryHW.pololu_servo.multi_servo_hw import PololuMaestroHW, PololuMaestroWheelServoHW, PololuMaestroShutterServoHW
        self.add_hardware(PololuMaestroHW(self, name='pololu_maestro'))
        self.add_hardware(PololuMaestroWheelServoHW(self, name='power_wheel', channel=0))

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))
        
        # from ScopeFoundryHW.thorlabs_powermeter.thorlabs_powermeter_analog_readout import ThorlabsPowerMeterAnalogReadOut
        # self.add_hardware(ThorlabsPowerMeterAnalogReadOut(self))
                
        # from ScopeFoundryHW.thorlabs_stepper_motors import ThorlabsStepperControllerHW
        # self.add_hardware(ThorlabsStepperControllerHW(self))
                
        from ScopeFoundryHW.thorlabs_integrated_stepper.thorlabs_integrated_stepper_motor_hw import ThorlabsIntegratedStepperMottorHW
        self.add_hardware_component(ThorlabsIntegratedStepperMottorHW(self))

        from ScopeFoundryHW.dli_powerswitch import DLIPowerSwitchHW
        dli = self.add_hardware(DLIPowerSwitchHW(self))
        
        from ScopeFoundryHW.thorlabs_ell6k_dual_position_slider.ell6k_dual_position_slider import ELL6KDualPositionSliderHW
        self.add_hardware(ELL6KDualPositionSliderHW(self, name='dual_position_slider'))
        
        # from ScopeFoundryHW.thorlabs_motorized_filter_flipper.thorlabsMFF_hardware import ThorlabsMFFHW
        # self.add_hardware_component(ThorlabsMFFHW(self))

        # from ScopeFoundryHW.chameleon_compact_opo.chameleon_compact_opo_hw import ChameleonCompactOPOHW
        # self.add_hardware(ChameleonCompactOPOHW(self))

        # from ScopeFoundryHW.keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        # self.add_hardware(KeithleySourceMeterComponent(self))

        # from ScopeFoundryHW.andor_camera import AndorCCDHW, AndorCCDReadoutMeasure
        # self.add_hardware(AndorCCDHW(self))
        # self.add_measurement(AndorCCDReadoutMeasure)

        #from ScopeFoundryHW.toupcam.toupcam_hw import ToupCamHW
        #self.add_hardware(ToupCamHW(self))

        # from ScopeFoundryHW.thorlabs_elliptec.elliptec_hw import ThorlabsElliptecSingleHW
        # self.add_hardware(ThorlabsElliptecSingleHW(self, name='polarizer'))

        # from ScopeFoundryHW.lakeshore_331.lakeshore_hw import Lakeshore331HW
        # self.add_hardware(Lakeshore331HW(self))

        print("Adding Measurement Components")

        # from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
        # self.add_measurement(HydraHarpOptimizerMeasure(self))
        
        # from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
        # self.add_measurement(HydraHarpHistogramMeasure(self))

        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement(PowerScanMeasure(self))

        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))

        # from measurements.laser_line_writer import LaserLineWriter
        # self.add_measurement(LaserLineWriter(self))

        # from ScopeFoundryHW.keithley_sourcemeter.iv_base_measurement import IVBaseMeasurement,IVTRPL
        # self.add_measurement(IVBaseMeasurement(self))
        # self.add_measurement(IVTRPL(self))

        # from ScopeFoundryHW.crystaltech_aotf.crystaltech_aotf_hc import CrystalTechAOTF
        # self.add_hardware(CrystalTechAOTF(self))

        # from ScopeFoundryHW.xbox_controller.xbox_controller_test_measure import
        # from confocal_measure.toupcam_spot_optimizer import AttocubeToupCamLive
        # self.add_measurement(AttocubeToupCamLive)

        #from confocal_measure.toupcam_spot_optimizer import ToupCamSpotOptimizer
        #self.add_measurement(ToupCamSpotOptimizer(self))
        
        # from confocal_measure.sequencer import Sequencer
        # self.add_measurement(Sequencer(self))
        
        # from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        # self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        # from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        # self.add_measurement_component(APDOptimizerCBMeasurement(self))  

        # from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo_hw import DynamixelXServosHW
        # from ScopeFoundryHW.dynamixel_servo.dynamixel_single_hw import DynamixelServoHW
        # servos = self.add_hardware(DynamixelXServosHW(self, devices=dict(power_wheel=10,)))
        # self.add_hardware(DynamixelServoHW(self, name='power_wheel'))        

    def setup_ui(self):
        '''sets up a quickbar'''
        Q = self.add_quickbar(load_qt_ui_file(sibling_path(__file__, 'quickbar.ui')))
        
        # Power wheel
        n = power_wheel_hardware_name = 'power_wheel'
        if n in self.hardware:
            PW = self.hardware[n]
            PWS = PW.settings

            def go_to(pos, PWS=PWS):
                PWS['target_position'] = pos

            Q.power_wheel_0_pushButton.clicked.connect(lambda x:go_to(0))
            Q.power_wheel_90_pushButton.clicked.connect(lambda x:go_to(90))
            Q.power_wheel_180_pushButton.clicked.connect(lambda x:go_to(180))
            Q.power_wheel_270_pushButton.clicked.connect(lambda x:go_to(270))
            Q.power_wheel_jog_forward_pushButton.clicked.connect(lambda x:PW.jog_forward)
            #PWS._jog_step.connect_to_widget(Q.power_wheel_jog_doubleSpinBox)
            #Q.power_wheel_jog_backward_pushButton.clicked.connect(lambda x:PW.jog_backward)
            PWS.position.connect_to_widget(Q.power_wheel_position_label)
            #PWS.target_position.connect_to_widget(Q.power_wheel_target_position_doubleSpinBox)
        else:
            Q.power_wheel_groupBox.setVisible(False)
        
        # Power meter
        n = 'thorlabs_powermeter'
        if n in self.hardware:
            PM = self.hardware[n]
            PMS = self.hardware.thorlabs_powermeter.settings
            PMS.connected.connect_to_widget(Q.power_meter_connected_checkBox)
            PMS.wavelength.connect_to_widget(Q.power_meter_wavelength_doubleSpinBox)        
            # PMS.power.connect_to_widget(Q.power_meter_power_label)
            from ScopeFoundry.helper_funcs import replace_widget_in_layout
            import pyqtgraph as pg
            W = replace_widget_in_layout(Q.power_meter_power_label, pg.widgets.SpinBox.SpinBox())
            PMS.power.connect_to_widget(W)
            if 'powermeter_optimizer' in self.measurements:
                M = self.measurements['powermeter_optimizer']
                M.settings.activation.connect_to_pushButton(Q.power_meter_activation_pushButton)
                Q.power_meter_show_ui_pushButton.clicked.connect(M.show_ui)
        else:
            Q.power_meter_groupBox.setVisible(False)

    def link_2D_scan_params(self, parent_scan_name='apd_asi',
                            children_scan_names=['hyperspec_asi', 'asi_trpl_2d_scan']):
        '''call this function to link equivalent settings of children scans to a parent scan'''
        lq_names = ['h0', 'h1', 'v0', 'v1', 'Nh', 'Nv']

        parent_scan = self.measurements[parent_scan_name]
        for scan in children_scan_names:
            child_scan = self.measurements[scan]
            for lq_name in lq_names:
                master_scan_lq = parent_scan.settings.get_lq(lq_name)
                child_scan.settings.get_lq(lq_name).connect_to_lq(master_scan_lq)
                
if __name__ == '__main__':
    import sys
    app = NikonMicroscope(sys.argv)
    app.settings_load_ini('defaults.ini')
    app.load_window_positions_json(r'window_positions.json')
    sys.exit(app.exec_())
