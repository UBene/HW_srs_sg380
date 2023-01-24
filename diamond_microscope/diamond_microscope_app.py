import logging

from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

logging.basicConfig(level='WARNING')
logging.getLogger("ipykernel").setLevel(logging.WARNING)
logging.getLogger('PyQt4').setLevel(logging.WARNING)
logging.getLogger('PyQt5').setLevel(logging.WARNING)
logging.getLogger('LoggedQuantity').setLevel(logging.WARNING)


class DiamondMicroscope(BaseMicroscopeApp):

    name = 'diamond_microscope'

    def setup(self):

        from ScopeFoundryHW.acton_spec import ActonSpectrometerHW
        self.add_hardware(ActonSpectrometerHW(self))

        from ScopeFoundryHW.thorlabs_powermeter import ThorlabsPowerMeterHW
        self.add_hardware_component(ThorlabsPowerMeterHW(self))

        # from ScopeFoundryHW.thorlabs_powermeter.thorlabs_powermeter_analog_readout import ThorlabsPowerMeterAnalogReadOut
        # self.add_hardware(ThorlabsPowerMeterAnalogReadOut(self))

        from ScopeFoundryHW.thorlabs_integrated_stepper.thorlabs_integrated_stepper_motor_hw import ThorlabsIntegratedStepperMottorHW
        self.add_hardware_component(ThorlabsIntegratedStepperMottorHW(self))

        from ScopeFoundryHW.thorlabs_powermeter import PowerMeterOptimizerMeasure
        self.add_measurement(PowerMeterOptimizerMeasure(self))

        # from confocal_measure.sequencer import SweepSequencer
        # self.add_measurement(SweepSequencer(self))

        # PM100A power meter
        # from ScopeFoundryHW.thorlabs_pm100a_fromCage import ThorlabsPowerMeterSiHW
        # self.add_hardware_component(ThorlabsPowerMeterSiHW(self))
        # from ScopeFoundryHW.thorlabs_pm100a_fromCage import PowerMeterOptimizerMeasure
        # self.add_measurement(PowerMeterOptimizerMeasure(self))

        # PI stage
        from ScopeFoundryHW.pi_xyz_stage.pi_xyz_stage_hw import PIXYZStageHW
        self.add_hardware(PIXYZStageHW(self))

        v_limits = h_limits = (0, 100)
        h_unit = v_unit = 'um'
        stage_inits = dict(h_limits=h_limits, v_limits=v_limits,
                           h_unit=h_unit, v_unit=v_unit)

        # APD
        from ScopeFoundryHW.ni_daq.hw.ni_freq_counter_callback import NI_FreqCounterCallBackHW
        self.add_hardware(NI_FreqCounterCallBackHW(self, name='apd_counter'))
        from confocal_measure.apd_optimizer_cb import APDOptimizerCBMeasurement
        self.add_measurement(APDOptimizerCBMeasurement(self))
        from confocal_measure.pi_xyz_scans.pi_xyz_2d_apd_slow_scan import PIXYZ2DAPDSlowScan
        self.add_measurement(PIXYZ2DAPDSlowScan(self, **stage_inits))

        # picam
        from ScopeFoundryHW.picam.picam_hw import PicamHW
        self.add_hardware(PicamHW(self))
        from ScopeFoundryHW.picam import PicamReadoutMeasure
        self.add_measurement(PicamReadoutMeasure(self))
        from confocal_measure.pi_xyz_scans.pi_xyz_2d_picam_slow_scan import PIXYZ2DPICAMSlowScan
        self.add_measurement(PIXYZ2DPICAMSlowScan(self, **stage_inits))

        # Timeharp
        from ScopeFoundryHW.picoquant import TimeHarp260HW, TimeHarpOptimizerMeasure, TimeHarpHistogramMeasure, Timeharp260TTTRMeasure
        self.add_hardware(TimeHarp260HW(self))
        self.add_measurement(TimeHarpOptimizerMeasure(self))
        self.add_measurement(TimeHarpHistogramMeasure(self))
        self.add_measurement(Timeharp260TTTRMeasure(self))

        # Hydraharp
        # from ScopeFoundryHW.picoquant.hydraharp_hw import HydraHarpHW
        # self.add_hardware(HydraHarpHW(self))
        # from ScopeFoundryHW.picoquant.hydraharp_optimizer import HydraHarpOptimizerMeasure
        # self.add_measurement(HydraHarpOptimizerMeasure(self))
        # from ScopeFoundryHW.picoquant.hydraharp_hist_measure import HydraHarpHistogramMeasure
        # self.add_measurement(HydraHarpHistogramMeasure(self))

        from confocal_measure.pi_xyz_scans.pi_xyz_2d_histogram_slow_scan import PIXYZ2DHistogramSlowScan
        self.add_measurement(PIXYZ2DHistogramSlowScan(self, **stage_inits))

        self.connect_scan_params('apd_2d_map',
                                 ['picam_2d_map',
                                  'histogram_2d_map'])

        from confocal_measure.calibration_sweep import CalibrationSweep
        self.add_measurement(CalibrationSweep(self))

        # from confocal_measure.power_scan import PowerScanMeasure
        # self.add_measurement(PowerScanMeasure(self))

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

        # from confocal_measure.toupcam_spot_optimizer import ToupCamSpotOptimizer
        # self.add_measurement(ToupCamSpotOptimizer(self))

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

        # SNSPD
        from ScopeFoundryHW.single_quantum.snspd import SNSPDHW, SNSPDOptimizerMeasure, SNSPDAquireCounts
        self.snspd_hw = self.add_hardware(SNSPDHW(self))
        self.add_measurement(SNSPDOptimizerMeasure(self))
        self.add_measurement(SNSPDAquireCounts(self))

        # Lucam
        from ScopeFoundryHW.lumera.lucam import LucamHW, LucamMeasure
        self.add_hardware(LucamHW(self))
        self.add_measurement(LucamMeasure(self))

        # Fiber alignment
        from confocal_measure.ranged_optimization import RangedOptimization
        optimization_choices = [
            (f"snspd {i}", f"hardware/snspd/count_rate_{i}") for i in range(self.snspd_hw.max_number_of_detectors)
        ] + [
            ("apd count rate", "hardware/apd_counter/count_rate"),
            ("timeharp CountRate0", "hardware/timeharp_260/CountRate0"),
            ("timeharp CountRate1", "hardware/timeharp_260/CountRate1"),
            ("timeharp SyncRate", "hardware/timeharp_260/SyncRate"),
            ("picoharp CountRate", "hardware/picoharp/count_rate"),
            # ("spotoptimizer 1/FWHM", "measure/toupcam_spot_optimizer/inv_FWHM"),
            # ("spotoptimizer max value", "measure/toupcam_spot_optimizer/max_val"),
            # ("spotoptimizer focus measure",
            #  "measure/toupcam_spot_optimizer/focus_measure"),
            # ("andor count rate (cont.)", "measure/andor_ccd_readout/count_rate"),
            ("picam count rate (cont.)", "measure/picam_readout/count_rate"),
        ]
        z_hw_choices = ('mdt69x_piezo_controller',)
        z_target_choices = ('x_target_position',
                            'y_target_position',
                            'z_target_position')
        z_choices = ('same_as_z_target',)
        self.add_measurement(RangedOptimization(self,
                                                name='fiber_alignment',
                                                optimization_choices=optimization_choices,
                                                z_hw_choices=z_hw_choices,
                                                z_target_choices=z_target_choices,
                                                z_choices=z_choices))

        # Picomotor
        from ScopeFoundryHW.new_focus_picomotor import PicomotorHW
        self.picomotor_hw = self.add_hardware(PicomotorHW(self))

        # T-cube dc servo motor
        from ScopeFoundryHW.thorlabs_tdc001_dc_servo_motor_driver import TDC001DCServoHW
        self.tcd_hw = self.add_hardware(TDC001DCServoHW(self))

        # Dc piezo controller
        from ScopeFoundryHW.thorlabs_mdt69x_piezo_controller import MDT69XHW, MDT69XBase2DSlowScan
        self.mdt69x_hw = self.add_hardware(MDT69XHW(self))
        self.add_measurement(MDT69XBase2DSlowScan(
            self, h_unit='V', v_unit='V'))

        # MFF
        from ScopeFoundryHW.thorlabs_motorized_filter_flipper.thorlabsMFF_hardware import ThorlabsMFFHW
        self.mff_hw = self.add_hardware(ThorlabsMFFHW(
            self, name='pinhole', position_choices=('in', 'out')))

        # Dual position slider
        from ScopeFoundryHW.thorlabs_ell6k_dual_position_slider import ELL6KDualPositionSliderHW
        self.ell_hw = self.add_hardware(
            ELL6KDualPositionSliderHW(self, choices=('A', 'B')))

    def connect_scan_params(self, parent_scan_name='apd_asi',
                            children_scan_names=['hyperspec_asi', 'asi_trpl_2d_scan']):
        lq_names = ['h0', 'h1', 'v0', 'v1', 'Nh', 'Nv']

        parent_scan = self.measurements[parent_scan_name]
        for scan in children_scan_names:
            child_scan = self.measurements[scan]
            for lq_name in lq_names:
                master_scan_lq = parent_scan.settings.get_lq(lq_name)
                child_scan.settings.get_lq(
                    lq_name).connect_to_lq(master_scan_lq)

    def setup_ui(self):
        from qtpy import QtWidgets
        widget = QtWidgets.QWidget()
        widget.setMaximumWidth(380)
        #widget.setContentsMargins(0, 0, 0, 0)
        #widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        layout = QtWidgets.QVBoxLayout(widget)
        self.add_quickbar(widget)

        layout.addWidget(self.picomotor_hw.New_quick_UI((1, 2, 3, 4)))
        layout.addWidget(self.tcd_hw.New_quick_UI())
        layout.addWidget(self.mdt69x_hw.New_quick_UI())
        layout.addWidget(self.mff_hw.New_quick_UI())
        layout.addWidget(self.ell_hw.New_quick_UI())
        return

        rainbow = '''qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 100), 
                        stop:0.166 rgba(255, 255, 0, 100), stop:0.333 rgba(0, 255, 0, 100), stop:0.5 rgba(0, 255, 255, 100), 
                        stop:0.666 rgba(0, 0, 255, 100), stop:0.833 rgba(255, 0, 255, 100), stop:1 rgba(255, 0, 0, 100))'''

        Q = self.add_quickbar(load_qt_ui_file(
            sibling_path(__file__, 'quickbar.ui')))

        # Power wheel
        if hasattr(self.hardware, 'power_wheel'):
            PW = self.hardware.power_wheel
            PWS = PW.settings

            def go_to(pos, PWS=PWS):
                PWS['target_position'] = pos

            Q.power_wheel_0_pushButton.clicked.connect(lambda x: go_to(0))
            Q.power_wheel_90_pushButton.clicked.connect(lambda x: go_to(90))
            Q.power_wheel_180_pushButton.clicked.connect(lambda x: go_to(180))
            Q.power_wheel_270_pushButton.clicked.connect(lambda x: go_to(270))
            Q.power_wheel_jog_forward_pushButton.clicked.connect(
                lambda x: PW.jog_forward)
            PWS.jog.connect_to_widget(Q.power_wheel_jog_doubleSpinBox)
            Q.power_wheel_jog_backward_pushButton.clicked.connect(
                lambda x: PW.jog_backward)
            PWS.position.connect_to_widget(Q.power_wheel_position_label)
            PWS.target_position.connect_to_widget(
                Q.power_wheel_target_position_doubleSpinBox)
        else:
            Q.power_wheel_groupBox.setVisible(False)

        # Power meter
        if hasattr(self.hardware, 'thorlabs_powermeter'):
            PM = self.hardware.thorlabs_powermeter
            PMS = self.hardware.thorlabs_powermeter.settings
            PMS.connected.connect_to_widget(Q.power_meter_connected_checkBox)
            PMS.wavelength.connect_to_widget(
                Q.power_meter_wavelength_doubleSpinBox)
            # PMS.power.connect_to_widget(Q.power_meter_power_label)
            from ScopeFoundry.helper_funcs import replace_widget_in_layout
            import pyqtgraph as pg
            W = replace_widget_in_layout(
                Q.power_meter_power_label, pg.widgets.SpinBox.SpinBox())
            PMS.power.connect_to_widget(W)
            M = self.measurements.powermeter_optimizer
            Q.power_meter_show_ui_pushButton.clicked.connect(M.show_ui)
        else:
            Q.power_meter_groupBox.setVisible(False)


if __name__ == '__main__':
    import sys
    app = DiamondMicroscope(sys.argv)
    app.settings_load_ini('defaults.ini')
    # app.load_window_positions_json(r'window_positions.json')
    sys.exit(app.exec_())
