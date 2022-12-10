from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level='DEBUG')
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)
logging.getLogger('pyvisa').setLevel(logging.WARNING)


class Microscope(BaseMicroscopeApp):

    name = 'upright_odmr_microscope'

    def setup(self):

        print("Adding Hardware Components")

        from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
        self.add_hardware(HydraHarpHW(self))

        # from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        # self.add_hardware(ActonSpectrometerHW(self))

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware(ThorlabsPowerMeterHW(self))
        # self.add_hardware(ThorlabsPowerMeterHW(self, name='thorlabs_powermeter_2'))
        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))
        # from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterAnalogReadOut
        # self.add_hardware(ThorlabsPowerMeterAnalogReadOut(self))

        # from ScopeFoundryHW.flip_mirror_arduino import FlipMirrorHW
        # self.add_hardware(FlipMirrorHW(self, name='flip_mirror'))

        # from ScopeFoundryHW.powerwheel_arduino import PowerWheelArduinoHW
        # self.add_hardware(PowerWheelArduinoHW(self, name='main_beam_power_wheel', conv=3200.0 / 360))
        # self.add_hardware(PowerWheelArduinoHW(self, name='side_beam_power_wheel', conv=3200.0 / 360))

        # from ScopeFoundryHW.thorlabs_integrated_stepper import ThorlabsIntegratedStepperMottorHW
        # self.add_hardware(ThorlabsIntegratedStepperMottorHW(self))

        # from ScopeFoundryHW.pi_spec import PISpectrometerHW
        # self.add_hardware(PISpectrometerHW(self))
        # from ScopeFoundryHW.picam.picam_hw import PicamHW
        # self.add_hardware(PicamHW(self))
        # from ScopeFoundryHW.picam import PicamReadoutMeasure
        # self.add_measurement(PicamReadoutMeasure(self))

        # from ScopeFoundryHW.pi_xyz_stage.pi_xyz_stage_hw import PIXYZStageHW
        # self.add_hardware(PIXYZStageHW)

        # from ScopeFoundryHW.dli_powerswitch.dlipower_hardware import DLIPowerSwitchHW
        # self.add_hardware(DLIPowerSwitchHW(self))

        # from ScopeFoundryHW.thorlabs_ell6k_dual_position_slider import ELL6KDualPositionSliderHW
        # self.add_hardware(ELL6KDualPositionSliderHW(self, name='dual_position_slider',
        #                                            choices=(('open', 1),
        #                                                     ('closed', 0))))

        # from ScopeFoundryHW.chameleon_compact_opo.chameleon_compact_opo_hw import ChameleonCompactOPOHW
        # self.add_hardware(ChameleonCompactOPOHW(self))

        # from ScopeFoundryHW.keithley_sourcemeter.keithley_sourcemeter_hc import KeithleySourceMeterComponent
        # self.add_hardware(KeithleySourceMeterComponent(self))

        # from ScopeFoundryHW.andor_camera import AndorCCDHW, AndorCCDReadoutMeasure
        # self.add_hardware(AndorCCDHW(self))
        # self.add_measurement(AndorCCDReadoutMeasure(self))

        from ScopeFoundryHW.toupcam.toupcam_hw import ToupCamHW
        self.add_hardware(ToupCamHW(self))

        from confocal_measure.toupcam_spot_optimizer import ToupCamSpotOptimizer
        self.add_measurement(ToupCamSpotOptimizer(self))

        # from ScopeFoundryHW.thorlabs_elliptec.elliptec_hw import ThorlabsElliptecSingleHW
        # self.add_hardware(ThorlabsElliptecSingleHW(self, name='polarizer'))

        from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
        self.add_measurement(HydraHarpOptimizerMeasure(self))

        # from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
        # self.add_measurement(HydraHarpHistogramMeasure(self))

        # from confocal_measure.power_scan import PowerScanMeasure
        # p = 'hardware/dual_position_slider/position'
        # self.add_measurement(PowerScanMeasure(self,
        #                                      shutter_open_lq_path=p))

        # from measurements.laser_line_writer import LaserLineWriter
        # self.add_measurement(LaserLineWriter(self))

        # from ScopeFoundryHW.keithley_sourcemeter.iv_base_measurement import IVBaseMeasurement,IVTRPL
        # self.add_measurement(IVBaseMeasurement(self))
        # self.add_measurement(IVTRPL(self))

        # from ScopeFoundryHW.crystaltech_aotf.crystaltech_aotf_hc import CrystalTechAOTF
        # self.add_hardware(CrystalTechAOTF(self))

        from confocal_measure.sequencer import SweepSequencer
        self.add_measurement(SweepSequencer(self))

        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement(APDOptimizerCBMeasurement(self))

        from ScopeFoundryHW.nidaqmx.galvo_mirrors.galvo_mirrors_hw import GalvoMirrorsHW
        self.add_hardware(GalvoMirrorsHW(self))

        from ScopeFoundryHW.nidaqmx.galvo_mirrors.galvo_mirror_2d_apd_slow_scan import GalvoMirrorAPDScanMeasure
        self.add_measurement(GalvoMirrorAPDScanMeasure(self))

        # from confocal_measure.calibration_sweep import CalibrationSweep
        # self.add_measurement(CalibrationSweep(self, 'calibration_sweep',
        #                                      'picam_readout', 'pi_spectrometer',))

        # from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo_hw import DynamixelXServosHW
        # from ScopeFoundryHW.dynamixel_servo.dynamixel_single_hw import DynamixelServoHW
        # servos = self.add_hardware(DynamixelXServosHW(self, devices=dict(focus_knob=50,
        #                                                                 power_wheel=51)))
        # self.add_hardware(DynamixelServoHW(self, name='focus_knob'))
        # self.add_hardware(DynamixelServoHW(self, name='power_wheel'))

        # from ScopeFoundryHW.lakeshore_335.lakeshore_hw import Lakeshore335HW
        # self.add_hardware(Lakeshore335HW(self))
        # from ScopeFoundryHW.lakeshore_335.lakeshore_measure import LakeshoreMeasure
        # self.add_measurement(LakeshoreMeasure(self))

        # from confocal_measure.generic_sweep import GenericSweeper
        # self.add_measurement(GenericSweeper(self))

        # from confocal_measure.ranged_optimization import RangedOptimization
        # self.add_measurement(RangedOptimization(self, name='auto_focus'))

        from ScopeFoundryHW.srs.SRS_HW import SRS
        self.add_hardware(SRS(self))

        named_channels_kwargs = [
            dict(name='DAQ_sig', initial=1, colors=['#32CA32'],
                 description='channel used to generate the pulses fed to the DAQ to gate/act to trigger signal.'),
            dict(name='DAQ_ref', initial=0, colors=['#7CFC00'],
                 description='channel used to generate the pulses fed to the DAQ to gate/act to trigger signal.'),
            dict(name='AOM', initial=2, colors=['b'],
                 description='channel connected to the TTL input of the switch used to switch on and off the radio-frequency drive to the Acousto Optic Modulator (AOM).'),
            dict(name='uW', initial=6, colors=['#FFA500'],
                 description='channel connected to the TTL input of the switch used to switch on and off the microwaves generated by the SRS microwave signal generator.'),
            dict(name='I', initial=4, colors=['#A52A2A'],
                 description='channel connected to the I (or "in phase") input of the SRS microwave signal generator.',),
            dict(name='Q', initial=5, colors=['#A020F0'],
                 description='channel connected to the Q (or "in quadrature") input of the SRS microwave signal generator.'),
            dict(name='sync_out', initial=3, colors=['#FFFF28'],
                 description='channel to synchronize external clocks, such as uW generator. (Not strictly required for most ODMR experiment)'),
            dict(name='dummy_channel', initial=18, colors=['#FFFF28'],
                 description='used to add delay to end of pulse program'),
        ]

        from ScopeFoundryHW.spincore.pulse_blaster_hw import PulseBlasterHW
        self.add_hardware(PulseBlasterHW(self, False, None, named_channels_kwargs, 500_000_000, 21))

        #from ScopeFoundryHW.nidaqmx.buffered_edge_smpl_clk_counter_hw import BufferedEdgeSmplClkCounterHW
        # self.add_hardware(BufferedEdgeSmplClkCounterHW(self))

        from ScopeFoundryHW.nidaqmx.pulse_width_counters_hw import PulseWidthCounters
        self.add_hardware(PulseWidthCounters(self))

        # from odmr_measurements.config_measurement import ConfigMeasurement
        # self.add_measurement(ConfigMeasurement(self))

        from odmr_measurements.esr import ESR
        self.add_measurement(ESR(self))

        from odmr_measurements.rabi import Rabi
        self.add_measurement(Rabi(self))

        from odmr_measurements.optimal_readout_delay import OptimalReadoutDelay
        self.add_measurement(OptimalReadoutDelay(self))

        from odmr_measurements.T1 import T1
        self.add_measurement(T1(self))

        from odmr_measurements.T2 import T2
        self.add_measurement(T2(self))

        from odmr_measurements.XY8 import XY8
        self.add_measurement(XY8(self))

        from odmr_measurements.correlation_spectroscopy import CorrelationSpectroscopy
        self.add_measurement(CorrelationSpectroscopy(self))

        from odmr_measurements.test_sig_ref_readout import SigRefReadout
        self.add_measurement(SigRefReadout(self))

        from confocal_measure.power_scan import PowerScanMeasure
        self.add_measurement(PowerScanMeasure(self))

        from ScopeFoundryHW.dynamixel_servo.dynamixel_x_servo_hw import DynamixelXServosHW
        from ScopeFoundryHW.dynamixel_servo.dynamixel_single_hw import DynamixelServoHW
        self.add_hardware(DynamixelXServosHW(self, devices=dict(focus_knob=50,
                                                                power_wheel=51)))
        self.add_hardware(DynamixelServoHW(self, name='focus_knob',
                                           lq_kwargs={'spinbox_decimals': 3,
                                                      'unit': 'um'}))
        self.add_hardware(DynamixelServoHW(self, name='power_wheel'))

        from odmr_measurements.iq_pulse_sweep import IQPulseSweep
        self.add_measurement(IQPulseSweep)

        from odmr_measurements.i_pulse_sweep import IPulseSweep
        self.add_measurement(IPulseSweep)

        from odmr_measurements.q_pulse_sweep import QPulseSweep
        self.add_measurement(QPulseSweep)

        from odmr_measurements.esr_sweep_ref_readout import ESRSweepRef
        self.add_measurement(ESRSweepRef(self))

    def setup_ui(self):
        pass
        '''sets up a quickbar'''
        Q = self.add_quickbar(load_qt_ui_file(
            sibling_path(__file__, 'quickbar.ui')))
        # # Dual position slider
        # DS = self.hardware.dual_position_slider.settings
        # DS.connected.connect_to_widget(Q.shutter_connected_checkBox)
        # DS.position.connect_to_widget(Q.shutter_open_comboBox)
        #
        # # Flip mirror
        # FS = self.hardware.flip_mirror.settings
        # FS.connected.connect_to_widget(Q.flip_mirror_connected_checkBox)
        # FS.position.connect_to_widget(Q.flip_mirror_position_checkBox)
        #
        # # DLI Power switch
        # widget = self.hardware.dli_powerswitch.new_mini_Widget()
        # Q.additional_widgets.addWidget(widget)
        #
        # # Power wheel
        # # n = 'main_beam_power_wheel'
        # n = 'power_wheel'
        # PW = self.hardware[n]
        # PWS = self.hardware[n].settings
        # PWS.connected.connect_to_widget(Q.power_wheel_connected_checkBox)
        # Q.power_wheel_jog_forward_pushButton.clicked.connect(lambda x:PW.jog_fwd())
        # PWS.jog.connect_to_widget(Q.power_wheel_jog_doubleSpinBox)
        # Q.power_wheel_jog_backward_pushButton.clicked.connect(lambda x:PW.jog_bkwd())
        # PWS.position.connect_to_widget(Q.power_wheel_position_label)
        # PWS.target_position.connect_to_widget(Q.power_wheel_target_position_doubleSpinBox)
        # update_value = PWS.target_position.update_value
        # Q.power_wheel_0_pushButton.clicked.connect(lambda x: update_value(0.1))
        # Q.power_wheel_90_pushButton.clicked.connect(lambda x: update_value(90))
        # Q.power_wheel_180_pushButton.clicked.connect(lambda x: update_value(180))
        # Q.power_wheel_270_pushButton.clicked.connect(lambda x: update_value(270))
        # Q.power_wheel_zero_encoder_pushButton.setVisible(False)
        # # Q.power_wheel_zero_encoder_pushButton.clicked.connect(lambda x:PW.zero_encoder())
        #
        # # Picam
        # S = self.hardware['picam'].settings
        # S.connected.connect_to_widget(Q.picam_connected_checkBox)
        #
        # S.ExposureTime.connect_to_widget(Q.picam_exposuretime_doubleSpinBox)
        # M = self.measurements['picam_readout']
        # Q.picam_show_ui_pushButton.clicked.connect(M.show_ui)
        # M.settings.count_rate.connect_to_widget(Q.picam_count_rate_doubleSpinBox)
        # M.settings.continuous.connect_to_widget(Q.picam_continuous_checkBox)
        #
        # # Spectrometer
        # S = self.hardware['pi_spectrometer'].settings
        # S.connected.connect_to_widget(Q.spectrometer_connected_checkBox)
        # S.center_wl.connect_to_widget(Q.spectrometer_center_wavelength_doubleSpinBox)
        #

        # APD
        from ScopeFoundry.helper_funcs import replace_widget_in_layout
        import pyqtgraph as pg
        S = self.hardware.apd_counter.settings
        S.connected.connect_to_widget(Q.apd_connected_checkBox)
        S.int_time.connect_to_widget(Q.apd_int_time_doubleSpinBox)
        W = replace_widget_in_layout(Q.apd_count_rate_doubleSpinBox,
                                     pg.widgets.SpinBox.SpinBox())
        S.count_rate.connect_to_widget(W)
        M = self.measurements['apd_optimizer']
        Q.apd_show_ui_pushButton.clicked.connect(M.show_ui)

        # Power meter
        # n = 'thorlabs_powermeter'
        # PMS = self.hardware[n].settings
        # PMS.connected.connect_to_widget(Q.power_meter_connected_checkBox)
        # PMS.wavelength.connect_to_widget(Q.power_meter_wavelength_doubleSpinBox)
        # W = replace_widget_in_layout(Q.power_meter_power_label,
        #                              pg.widgets.SpinBox.SpinBox())
        # PMS.power.connect_to_widget(W)
        # if 'powermeter_optimizer' in self.measurements:
        #     M = self.measurements['powermeter_optimizer']
        #     M.settings.activation.connect_to_pushButton(Q.power_meter_activation_pushButton)
        #     Q.power_meter_show_ui_pushButton.clicked.connect(M.show_ui)
        #
        # TS = self.hardware.toupcam.settings
        # TS.connected.connect_to_widget(Q.toupcam_connected_checkBox)
        # M = self.measurements['toupcam_spot_optimizer']
        # M.settings.activation.connect_to_widget(Q.toupcam_live_checkBox)
        # Q.toupcam_show_ui_pushButton.clicked.connect(M.show_ui)
        #
        # knob = self.hardware.focus_knob
        # S = knob.settings
        # S.connected.connect_to_widget(Q.focus_wheel_connected_checkBox)
        # S.position.connect_to_widget(Q.focus_wheel_position_doubleSpinBox)
        # S.target_position.connect_to_widget(Q.focus_wheel_target_position_doubleSpinBox)
        # S.jog.connect_to_widget(Q.focus_wheel_jog_doubleSpinBox)
        # Q.focus_wheel_foreward_pushButton.clicked.connect(knob.jog_fwd)
        # Q.focus_wheel_backward_pushButton.clicked.connect(knob.jog_bkwd)

    def link_2D_scan_params(self, parent_scan_name='apd_asi',
                            children_scan_names=['hyperspec_asi', 'asi_trpl_2d_scan']):
        '''call this function to link equivalent settings of children scans to a parent scan'''
        lq_names = ['h0', 'h1', 'v0', 'v1', 'Nh', 'Nv']

        parent_scan = self.measurements[parent_scan_name]
        for scan in children_scan_names:
            child_scan = self.measurements[scan]
            for lq_name in lq_names:
                master_scan_lq = parent_scan.settings.get_lq(lq_name)
                child_scan.settings.get_lq(
                    lq_name).connect_to_lq(master_scan_lq)


if __name__ == '__main__':
    import sys
    app = Microscope(sys.argv)
    app.settings_load_ini('defaults.ini')
    # app.load_window_positions_json(r'window_positions.json')
    sys.exit(app.exec_())
