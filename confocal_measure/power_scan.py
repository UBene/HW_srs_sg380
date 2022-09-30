from ScopeFoundry import Measurement
import numpy as np
import time
from ScopeFoundry import h5_io
from ScopeFoundry.helper_funcs import sibling_path
import pyqtgraph as pg
from qtpy import QtWidgets
import datetime
import os


class PowerScanMeasure(Measurement):

    name = 'power_scan'

    def __init__(self, app, shutter_open_lq_path=None):
        self.ui_filename = sibling_path(__file__, "power_scan.ui")
        Measurement.__init__(self, app)
        if shutter_open_lq_path != None:
            self.shutter_open = app.lq_path(shutter_open_lq_path)

    def setup(self):

        self.power_wheel_range = self.settings.New_Range('power_wheel', include_sweep_type=True,
                                                         initials=[0, 280, 28])
        self.power_wheel_range.sweep_type.update_value('up_down')
        self.settings.New('acq_mode', dtype=str, initial='const_time',
                          choices=('const_time', 'const_dose', 'manual_acq_times'))

        self.settings.New('manual_acq_times', str, initial='0,5; 20,2; 100,1')
        self.settings.New('collection_delay', initial=0.01, unit='s',
                          description='after setting the wheel, data collection is delayed to reach steady state')

        # possible hardware components and their integration times setting:
        self.hws = {'picoharp': 'Tacq',
                    'hydraharp': 'Tacq',
                    'ascom_img': 'exp_time',
                    'andor_ccd': 'exposure_time',
                    'winspec_remote_client': 'acq_time',
                    'apd_counter': 'int_time',
                    'picam': 'ExposureTime',
                    'thorlabs_powermeter_2': 'average_count',
                    'labspec': 'exposure_time',
                    'rabi': 'N_samples',
                    }
        

        for key in self.hws.keys():
            self.settings.New('collect_{}'.format(key),
                              dtype=bool, initial=False)

            
        self.settings.New("x_axis", dtype=str, initial='pm_power',
                          choices=('power_wheel_positions', 'power'))
        self.settings.New('use_shutter', dtype=bool, initial=False)
        self.settings.New('swap_reflector', dtype=bool, initial=False)
        self.settings.New('reflector_swap_duration', initial=1.2, unit='sec',
                          description='time for reflector to swap')
        self.settings.New('opt_period', int, initial=-1, unit='steps',
                          description='''set -1 to disable periodic calling 
                                         of optimize_at_opt_pw_pos function. 
                                         This feature might NOT work on your setup.''')
        self.settings.New('opt_pw_pos', float, initial=-1.0,
                          description='''power_wheel position at which the optimization is performed.
                                         set to -1.0 to choose current position.''')
        self.settings.New('opt_measure', str, initial='auto_focus',
                          description='''Choose the measurement that executes the optimization. 
                                          NOTE that this feature might NOT work on your setup.
                                          Check self.optimize_at_opt_pw_pos.''')
        self.settings.New('wheel_hw', dtype=str, initial='power_wheel',
                          choices=['power_wheel', 'polarizer',
                                   'elliptec', 'motorized_polarizer',
                                   'main_beam_power_wheel',
                                   'side_beam_power_wheel'],
                          description='Choose the hardware used to modulate the power.')

        self.settings.New('power_meter_sample_number', int, initial=10,
                          description='Choose how many times the powermeter is being asked for a reading.')

        self.settings.New('polling_powers', bool, initial=False)
        self.settings.New('new_folder', bool, initial=False)

    def setup_figure(self):

        self.settings.activation.connect_to_pushButton(
            self.ui.start_pushButton)
        self.settings.x_axis.connect_to_widget(self.ui.x_axis_comboBox)
        self.settings.x_axis.add_listener(self.update_display)
        self.settings.acq_mode.connect_to_widget(self.ui.acq_mode_comboBox)

        self.ui.power_scan_GroupBox.layout().addWidget(
            QtWidgets.QLabel('optimize period'))
        period_widget = QtWidgets.QDoubleSpinBox(decimals=0)
        self.settings.opt_period.connect_to_widget(period_widget)
        self.ui.power_scan_GroupBox.layout().addWidget(period_widget)

        self.ui.power_scan_GroupBox.layout().addWidget(
            QtWidgets.QLabel('opt power wheel pos'))
        opt_pw_pos_widget = QtWidgets.QDoubleSpinBox(decimals=0)
        self.settings.opt_pw_pos.connect_to_widget(opt_pw_pos_widget)
        self.ui.power_scan_GroupBox.layout().addWidget(opt_pw_pos_widget)

        if hasattr(self, 'shutter_open'):
            CB_widget = QtWidgets.QCheckBox('use shutter')
            self.settings.use_shutter.connect_to_widget(CB_widget)
            self.ui.power_scan_GroupBox.layout().addWidget(CB_widget)
        else:
            self.settings['use_shutter'] = False
            self.settings.use_shutter.change_readonly(True)

        self.settings.manual_acq_times.connect_to_widget(
            self.ui.manual_acq_times_lineEdit)
        self.ui.manual_acq_times_lineEdit.setVisible(False)
        self.settings.acq_mode.add_listener(self.on_change_acq_mode)

        self.power_wheel_range.min.connect_to_widget(
            self.ui.power_wheel_min_doubleSpinBox)
        self.power_wheel_range.max.connect_to_widget(
            self.ui.power_wheel_max_doubleSpinBox)
        self.power_wheel_range.num.connect_to_widget(
            self.ui.power_wheel_num_doubleSpinBox)
        self.power_wheel_range.step.connect_to_widget(
            self.ui.power_wheel_step_doubleSpinBox)
        self.power_wheel_range.sweep_type.connect_to_widget(
            self.ui.sweep_type_comboBox)

        # Hardware connections
        layout = self.ui.collect_groupBox.layout()
        # self.app.measurements.keys()
        self.installed_hw = {}

        for key in self.hws.keys():
            if key in self.app.hardware.keys():
                Tacq_lq = getattr(
                    self.app.hardware[key].settings, self.hws[key])
                
                
            elif key in self.app.measurements.keys():
                Tacq_lq = getattr(
                    self.app.measurements[key].settings, self.hws[key])
            else:
                continue
                                            
            CB_widget = QtWidgets.QCheckBox(key)
            lq = getattr(self.settings, 'collect_{}'.format(key))
            lq.connect_to_widget(CB_widget)
            SP_widget = QtWidgets.QDoubleSpinBox()
            Tacq_lq.connect_to_widget(SP_widget)
            layout.addRow(CB_widget, SP_widget)
            self.installed_hw.update({key: Tacq_lq})

        # Plot
        if hasattr(self, 'graph_layout'):
            # see
            # http://stackoverflow.com/questions/9899409/pyside-removing-a-widget-from-a-layout
            self.graph_layout.deleteLater()
            del self.graph_layout
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        self.power_plot = self.graph_layout.addPlot(title="Power Scan")
        self.power_plot.setLogMode(True, True)
        self.power_plot.showGrid(True, True)
        self.display_ready = False
        self.status = {'title': 'starting power scan', 'color': 'y'}

    def on_change_acq_mode(self):
        if self.settings['acq_mode'] == 'manual_acq_times':
            self.ui.manual_acq_times_lineEdit.setVisible(True)
        else:
            self.ui.manual_acq_times_lineEdit.setVisible(False)

    def pre_run(self):
        self.microscope_specific_pre_run()
        self.display_ready = False

        # Prepare data arrays and links to components:
        self.power_wheel_position = self.power_wheel_range.sweep_array
        self.Np = Np = len(self.power_wheel_position)

        self.pm_powers = np.zeros(Np, dtype=float)
        self.pm_powers_after = np.zeros(Np, dtype=float)

        self.power_wheel_hw = self.app.hardware[self.settings['wheel_hw']]

        if 'target_position' in self.power_wheel_hw.settings:
            self.pw_target_position = self.power_wheel_hw.settings.get_lq(
                'target_position')
        else:
            self.pw_target_position = self.power_wheel_hw.settings.get_lq(
                'position')

        self.power_wheel_hw.settings['connected'] = True
        self.pm_hw = self.app.hardware['thorlabs_powermeter']
        self.pm_hw.settings['connected'] = True

        self.used_hws = {}

        if self.settings['collect_apd_counter']:
            self.apd_counter_hw = self.app.hardware.apd_counter
            self.apd_count_rate_lq = self.apd_counter_hw.settings.count_rate
            self.apd_count_rates = np.zeros(Np, dtype=float)
            self.used_hws.update(
                {'apd_counter': self.installed_hw['apd_counter']})

        if self.settings['collect_picoharp']:
            self.ph_hw = self.app.hardware['picoharp']
            self.ph_hw.settings['connected'] = True
            Nt = self.ph_hw.settings['histogram_channels']
            self.picoharp_time_array = np.zeros(Nt, dtype=float)
            self.picoharp_elapsed_time = np.zeros(Np, dtype=float)
            self.picoharp_histograms = np.zeros((Np, Nt), dtype=int)
            self.used_hws.update({'picoharp': self.installed_hw['picoharp']})

        if self.settings['collect_hydraharp']:
            self.hh_hw = self.app.hardware['hydraharp']
            self.hh_hw.update_HistogramBins()
            self.hh_hw.settings['connected'] = True
            shape = self.hh_hw.hist_shape
            self.hydraharp_time_array = np.zeros(shape[-1], dtype=float)
            self.hydraharp_elapsed_time = np.zeros(Np, dtype=float)
            self.hydraharp_histograms = np.zeros((Np,) + shape, dtype=float)
            self.used_hws.update({'hydraharp': self.installed_hw['hydraharp']})

        # TODO: Can not currently take spectra from different cameras simultaneously because arrays are
        # are named the same for all cameras...
        if self.settings['collect_winspec_remote_client']:
            self.spec_readout = self.app.measurements['winspec_readout']
            self.spec_readout.settings['save_h5'] = False
            self.spectra = []  # don't know size of ccd until after measurement
            self.integrated_spectra = []
            self.used_hws.update(
                {'winspec_remote_client': self.installed_hw['winspec_remote_client']})

        if self.settings['collect_andor_ccd']:
            self.andor_readout = self.app.measurements['andor_ccd_readout']
            self.andor_readout.start_stop(False)
            self.andor_readout.settings['save_h5'] = False
            self.spectra = []  # don't know size of ccd until after measurement
            self.integrated_spectra = []
            self.used_hws.update({'andor_ccd': self.installed_hw['andor_ccd']})

        if self.settings['collect_ascom_img']:
            self.ascom_camera_capture = self.app.measurements.ascom_camera_capture
            self.ascom_camera_capture.settings['continuous'] = False
            self.ascom_img_stack = []
            self.ascom_img_integrated = []
            self.used_hws.update({'ascom_img': self.installed_hw['ascom_img']})

        if self.settings['collect_picam']:
            self.picam_readout = self.app.measurements['picam_readout']
            self.picam_readout.start_stop(False)
            self.picam_readout.settings['save_h5'] = False
            self.spectra = []  # don't know size of ccd until after measurement
            self.integrated_spectra = []
            self.used_hws.update({'picam': self.installed_hw['picam']})

        if self.settings['collect_thorlabs_powermeter_2']:
            self.pm2_hw = self.app.hardware.thorlabs_powermeter_2
            self.pm2_power = self.pm2_hw.settings.power
            self.pm2_powers = []
            self.used_hws.update(
                {'thorlabs_powermeter_2': self.installed_hw['thorlabs_powermeter_2']})

        if self.settings['collect_labspec']:
            self.labspec_readout = self.app.measurements['labspec_readout']
            self.labspec_readout.start_stop(False)
            self.labspec_readout.settings['save_h5'] = False
            self.spectra = []  # don't know size of ccd until after measurement
            self.integrated_spectra = []
            self.used_hws.update({'labspec': self.installed_hw['labspec']})

        if self.settings['collect_rabi']:
            self.rabi = self.app.measurements['rabi']
            # self.rabi.start_stop(False)
            # self.rabi.settings['save_h5'] = False
            # self.spectra = []  # don't know size of ccd until after measurement
            # self.integrated_spectra = []
            self.used_hws.update({'rabi': self.installed_hw['rabi']})


        # Prepare for different acquisition modes
        # if self.settings['acq_mode'] == 'const_SNR':
        #    self.spec_acq_times_array = self.spec_acq_time.val / np.exp(2*self.log_power_index)
        #    self.lifetime_acq_times_array = self.lifetime_acq_time.val / np.exp(2*self.log_power_index)

        if self.settings['use_shutter']:
            self.shutter_open.update_value(True)

        self.total_acquisition_time = 0
        self.Tacq_arrays = []

        if self.settings['acq_mode'] == 'const_dose':
            self.dose_calibration_data = self.acquire_dose_calibration_data()
            for hw, Tacq_lq in self.used_hws.items():
                acq_times_array = self.calc_acq_times_array_const_dose_calibrated(
                    Tacq_lq.val, self.dose_calibration_data)
                self.Tacq_arrays.append((hw, Tacq_lq, acq_times_array))
                # print(hw, 'acquisition time', acq_times_array.sum())
                self.total_acquisition_time += acq_times_array.sum()

        elif self.settings['acq_mode'] == 'manual_acq_times':
            # Note: all hw will use the same list and hence same acquisition times.
            #        Simple fix idea: scale acq_times_array with Tacq_lq.val
            string = self.settings['manual_acq_times']
            pos_vs_acqtime = np.array(np.matrix(string))
            for hw, Tacq_lq in self.used_hws.items():
                acq_times_array = self.calc_acq_times_array_manual_input(
                    pos_vs_acqtime)
                # acq_times_array *= Tacq.val
                self.Tacq_arrays.append((hw, Tacq_lq, acq_times_array))
                self.total_acquisition_time += acq_times_array.sum()

        elif self.settings['acq_mode'] == 'const_time':
            for hw, Tacq_lq in self.used_hws.items():
                # easy peasy const time array.
                acq_times_array = np.ones_like(
                    self.power_wheel_position) * Tacq_lq.val
                self.Tacq_arrays.append((hw, Tacq_lq, acq_times_array))
                self.total_acquisition_time += acq_times_array.sum()

        if self.settings['collect_picam']:
            self.total_acquisition_time /= 1000

        self.ii = 0

        # prepare plot curves
        self.power_plot.clear()
        self.plot_lines = []
        N_plot_lines = len(self.used_hws.keys())
        for i in range(N_plot_lines):
            c = (i + 1) / N_plot_lines
            self.plot_lines.append(
                self.power_plot.plot([1, 3, 2, 4], symbol='o'))
        self.display_ready = True

        if self.settings['new_folder']:
            self.root_folder = self.app.settings['save_dir']
            new_folder = os.path.join(self.root_folder, str(time.time()))
            os.mkdir(new_folder)
            self.app.settings['save_dir'] = new_folder


    def post_run(self):
        self.display_ready = False
        if self.settings['use_shutter']:
            self.shutter_open.update_value(False)
        self.update_display()
        self.microscope_specific_post_run()
        
        
        if self.settings['new_folder']:
            self.app.settings['save_dir'] = self.root_folder
        
        
    # def run(self):
    #     print(self.name)

    def run(self):

        S = self.settings

        if len(self.used_hws) == 0:
            self.status = {
                'title': 'Select a Collection Option and press Start', 'color': 'r'}
            return
        else:
            total_collection_delay = len(
                self.power_wheel_position) * self.settings['collection_delay']
            pm_collection_delay_per_step = S['power_meter_sample_number'] * \
                self.pm_hw.settings.average_count.val * 0.004

            if S['swap_reflector']:
                pm_collection_delay_per_step += 2 * \
                    S['reflector_swap_duration']

            total_powermeter_collection_time = len(
                self.power_wheel_position) * pm_collection_delay_per_step

            # Total estimated time
            ETR = datetime.timedelta(seconds=int(
                self.total_acquisition_time + total_collection_delay + total_powermeter_collection_time))
            self.status = {'title': 'ETR {}'.format(str(ETR)), 'color': 'g'}

        self.move_to_min_pos()

        self.polling_powers = []

        # loop through power wheel positions and measure active components.
        for ii in range(self.Np):

            self.ii = ii

            self.polling_powers.append([])

            self.settings['progress'] = 100. * ii / self.Np
            self.status = {'title': 'ETR {}'.format(
                str(ETR * (1 - ii / self.Np))), 'color': 'g'}

            if self.interrupt_measurement_called:
                break

            for hw, Tacq_lq, acq_times_array in self.Tacq_arrays:
                #print("power scan {} of {}, {} acq_times {}".format(ii + 1, self.Np, hw, acq_times_array[ii]))
                Tacq_lq.update_value(acq_times_array[ii])

            self.optimize_if_applicable(ii)

            print("moving power wheel to " + str(self.pw_target_position.value))

            self.pw_target_position.update_value(self.power_wheel_position[ii])
            print(self.name, 'moved target position',
                  self.power_wheel_position[ii])

            time.sleep(S['collection_delay'])
            # collect power meter value
            if S['swap_reflector']:
                self.swap_reflector_and_collect_power(ii)
            else:
                self.pm_powers[ii] = self.collect_pm_power_data()

            # read detectors
            if self.settings['collect_apd_counter']:
                time.sleep(self.apd_counter_hw.settings['int_time'])
                self.apd_count_rates[ii] = \
                    self.apd_counter_hw.settings.count_rate.read_from_hardware()

            if self.settings['collect_picoharp']:
                ph = self.ph_hw.picoharp
                ph.start_histogram()
                while not ph.check_done_scanning():
                    if self.interrupt_measurement_called:
                        break
                    ph.read_histogram_data()
                    time.sleep(0.1)
                ph.stop_histogram()
                ph.read_histogram_data()
                Nt = self.ph_hw.settings['histogram_channels']
                self.picoharp_elapsed_time[ii] = ph.read_elapsed_meas_time()
                self.picoharp_histograms[ii, :] = ph.histogram_data[0:Nt]
                self.picoharp_time_array = ph.time_array[0:Nt]

            if self.settings['collect_hydraharp']:
                self.hydraharp_histograms[ii,
                                          :] = self.aquire_histogram(self.hh_hw)
                self.hydraharp_time_array = self.hh_hw.sliced_time_array
                self.hydraharp_elapsed_time[ii] = self.hh_hw.settings['ElapsedMeasTime']

            if self.settings['collect_winspec_remote_client']:
                # self.spec_readout.run()
                self.spec_readout.settings['continuous'] = False
                self.spec_readout.settings['save_h5'] = False

                self.spec_readout.interrupt_measurement_called = False
                self.spec_readout.run()
                time.sleep(0.5)
                Tacq_lq = self.installed_hw['winspec_remote_client']
                # time.sleep(Tacq_lq.val)
                spec = np.array(self.spec_readout.data)
                if not (spec == None).any():
                    self.spectra.append(spec)
                    self.integrated_spectra.append(spec.sum())

            if self.settings['collect_andor_ccd']:
                self.andor_readout.settings['continuous'] = False
                if self.settings['polling_powers']:
                    self.start_nested_measure_and_wait(self.andor_readout, nested_interrupt=False,
                                                       polling_func=self.power_polling, polling_time=0.001)
                else:
                    self.start_nested_measure_and_wait(
                        self.andor_readout, nested_interrupt=False)
                spec = self.andor_readout.get_spectrum()
                if not (spec == None).any():
                    self.spectra.append(spec)
                    self.integrated_spectra.append(spec.sum())

            if self.settings['collect_ascom_img']:
                self.ascom_camera_capture.interrupt_measurement_called = False
                self.ascom_camera_capture.run()
                img = self.ascom_camera_capture.img.copy(
                ) / self.ascom_camera_capture.settings['exp_time']
                self.ascom_img_stack.append(img)
                self.ascom_img_integrated.append(img.astype(float).sum())

            if self.settings['collect_picam']:
                self.picam_readout.settings['continuous'] = False
                if self.settings['polling_powers']:
                    self.start_nested_measure_and_wait(self.picam_readout, nested_interrupt=False,
                                                       polling_func=self.power_polling, polling_time=0.001)
                else:
                    self.start_nested_measure_and_wait(
                        self.picam_readout, nested_interrupt=False)
                spec = self.picam_readout.get_spectrum()
                if not (spec == None).any():
                    self.spectra.append(spec)
                    self.integrated_spectra.append(spec.sum())

            if self.settings['collect_thorlabs_powermeter_2']:
                power = self.pm2_hw.power.read_from_hardware()
                self.pm2_powers.append(power)

            if self.settings['collect_labspec']:
                if self.settings['polling_powers']:
                    self.start_nested_measure_and_wait(self.labspec_readout, nested_interrupt=False,
                                                       polling_func=self.power_polling, polling_time=0.001)
                else:
                    self.start_nested_measure_and_wait(
                        self.labspec_readout, nested_interrupt=False)
                spec = self.labspec_readout.data['spectrum']
                if not (spec == None).any():
                    self.spectra.append(spec)
                    self.integrated_spectra.append(spec.sum())
                    
                    
            if self.settings['collect_rabi']:
                self.start_nested_measure_and_wait(self.rabi, nested_interrupt=False)
                

            # collect power meter value after measurement W/O SWAPPING
            self.pm_powers_after[ii] = self.collect_pm_power_data()

        self.status = {'title': 'Power scan finished', 'color': 'y'}
        self.save_h5()
        self.microscope_specific_post_run()

    def save_h5(self):
        # write data to h5 file on disk
        self.t0 = time.time()
        self.h5_file = h5_io.h5_base_file(app=self.app, measurement=self)
        try:
            self.h5_file.attrs['time_id'] = self.t0
            H = self.h5_meas_group = h5_io.h5_create_measurement_group(
                self, self.h5_file)

            if self.settings['collect_apd_counter']:
                H['apd_count_rates'] = self.apd_count_rates

            if self.settings['collect_picoharp']:
                H['picoharp_elapsed_time'] = self.picoharp_elapsed_time
                H['picoharp_histograms'] = self.picoharp_histograms
                H['picoharp_time_array'] = self.picoharp_time_array

            if self.settings['collect_hydraharp']:
                H['hydraharp_elapsed_time'] = self.hydraharp_elapsed_time
                H['hydraharp_histograms'] = self.hydraharp_histograms
                H['hydraharp_time_array'] = self.hydraharp_time_array

            if self.settings['collect_winspec_remote_client']:
                H['wls'] = self.spec_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)

            if self.settings['collect_andor_ccd']:
                H['wls'] = self.andor_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)

            if self.settings['collect_ascom_img']:
                H['ascom_img_stack'] = np.array(self.ascom_img_stack)
                H['ascom_img_integrated'] = np.array(self.ascom_img_integrated)

            if self.settings['collect_picam']:
                H['wls'] = self.picam_readout.wls
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)

            if self.settings['collect_labspec']:
                H['wls'] = self.labspec_readout.data['wavelengths']
                H['spectra'] = np.squeeze(np.array(self.spectra))
                H['integrated_spectra'] = np.array(self.integrated_spectra)

            if self.settings['collect_thorlabs_powermeter_2']:
                H['thorlabs_powermeter_2_powers'] = self.pm2_powers

            H['pm_powers'] = self.pm_powers
            H['pm_powers_after'] = self.pm_powers_after
            H['power_wheel_position'] = self.power_wheel_position
            max_entries = 0
            for powers in self.polling_powers:
                max_entries = max(len(powers), max_entries)
            H['polling_powers'] = np.array(
                [powers + [0] * (max_entries - len(powers)) for powers in self.polling_powers])
            H['avg_polling_powers'] = np.array(
                [np.mean(powers) for powers in self.polling_powers])
            for hw, Tacq_lq, acq_times_array in self.Tacq_arrays:
                H[hw + '_acq_times_array'] = acq_times_array
                print('saving ' + hw + '_acq_times_array')

        finally:
            self.log.info("data saved " + self.h5_file.filename)
            self.h5_file.close()

    def microscope_specific_pre_run(self):
        # update hardware settings (microscope specific)
        if 'lakeshore_measure' in self.app.measurements and 'lakeshore335' in self.app.hardware:
            if self.app.hardware.lakeshore335.settings['connected']:
                self.app.measurements.lakeshore_measure.settings['activation'] = True
                self.app.measurements.lakeshore_measure.set_history_start()
        if 'rigol_waveform_generator' in self.app.hardware:
            self.app.hardware.rigol_waveform_generator.read_from_hardware()

    def microscope_specific_post_run(self):
        if 'lakeshore_measure' in self.app.measurements:
            if self.app.hardware.lakeshore335.settings['connected']:
                self.app.measurements.lakeshore_measure.save_history()

    def power_polling(self):
        pm = self.app.hardware['thorlabs_powermeter']
        power = pm.settings.power.read_from_hardware()
        self.polling_powers[self.ii].append(power)

    def update_display(self):

        self.power_plot.setTitle(**self.status)

        if self.display_ready:

            ii = self.ii
            if self.settings['x_axis'] == 'power':
                X = self.pm_powers[:ii]
            else:
                X = self.power_wheel_position[:ii]

            jj = 0
            # update curves (order matters, as acq_times_array =
            # self.Tacq_arrays[jj][2] is used)
            if self.settings['collect_picoharp']:
                self.plot_lines[jj].setData(X, self.picoharp_histograms[:ii, :].sum(
                    axis=1) / self.picoharp_elapsed_time[:ii])
                jj += 1

            if self.settings['collect_hydraharp']:
                Y = self.hydraharp_histograms[:ii].sum(
                    axis=(1, 2)) / self.hydraharp_elapsed_time[:ii]
                self.plot_lines[jj].setData(X, Y)
                jj += 1

            if self.settings['collect_ascom_img']:
                self.plot_lines[jj].setData(X, self.ascom_img_integrated[:ii])
                self.ascom_camera_capture.update_display()
                jj += 1

            if self.settings['collect_andor_ccd']:
                acq_times_array = self.Tacq_arrays[jj][2]
                self.plot_lines[jj].setData(
                    X, self.integrated_spectra[:ii] / acq_times_array[:ii])
                jj += 1

            if self.settings['collect_winspec_remote_client']:
                acq_times_array = self.Tacq_arrays[jj][2]
                self.plot_lines[jj].setData(
                    X, self.integrated_spectra[:ii] / acq_times_array[:ii])
                jj += 1

            if self.settings['collect_apd_counter']:
                self.plot_lines[jj].setData(X, self.apd_count_rates[:ii])
                jj += 1

            if self.settings['collect_picam']:
                acq_times_array = self.Tacq_arrays[jj][2]
                self.plot_lines[jj].setData(
                    X, self.integrated_spectra[:ii] / acq_times_array[:ii])
                jj += 1

            if self.settings['collect_thorlabs_powermeter_2']:
                self.plot_lines[jj].setData(X, self.pm2_powers[:ii])
                jj += 1

            if self.settings['collect_labspec']:
                acq_times_array = self.Tacq_arrays[jj][2]
                self.plot_lines[jj].setData(
                    X, self.integrated_spectra[:ii] / acq_times_array[:ii])
                jj += 1

    def aquire_histogram(self, hw):
        hw.start_histogram()
        while not hw.check_done_scanning():
            if self.interrupt_measurement_called:
                break
            self.hist_data = np.array(
                hw.read_histogram_data(clear_after=False))
            time.sleep(5e-3)
        hw.stop_histogram()
        self.hist_data = np.array(hw.read_histogram_data(clear_after=True))

        # print(self.hist_data.shape, hw.hist_slice)
        hist_data = self.hist_data[hw.hist_slice]

        # print('aquire_histogram', hw.name, hist_data.sum())
        return hist_data

    def move_to_min_pos(self):
        self.pw_target_position.update_value(self.settings['power_wheel_min'])
        time.sleep(2.0)

    def collect_pm_power_data(self):
        PM_SAMPLE_NUMBER = self.settings['power_meter_sample_number']

        # Sample the power at least one time from the power meter.
        samp_count = 0
        pm_power = 0.0
        t0 = time.time()
        for samp in range(0, PM_SAMPLE_NUMBER):
            # Try at least 10 times before ultimately failing
            if self.interrupt_measurement_called:
                break
            try_count = 0
            # print "samp", ii, samp, try_count, samp_count, pm_power
            while not self.interrupt_measurement_called:
                try:
                    pm_power = pm_power + \
                        self.pm_hw.power.read_from_hardware(send_signal=True)
                    samp_count = samp_count + 1
                    break
                except Exception as err:
                    try_count = try_count + 1
                    if try_count > PM_SAMPLE_NUMBER - 1:
                        print("failed to collect power meter sample:", err)
                        break

            # print(f'averaged power={pm_power/samp_count:1.4}, success full readouts: {samp_count} at t={time.time()-t0:1.4}s', )
            ac = self.pm_hw.settings.average_count.val
            # the powermeter needs 3ms to probe a power. It internally averages
            # *ac* times.
            time.sleep(ac * 0.004)

        if samp_count > 0:
            pm_power = pm_power / samp_count
        else:
            print(self.name, "  Failed to read power")
            pm_power = 10000.

        return pm_power

    def acquire_dose_calibration_data(self):
        print('calibrating dose')
        dose_calibration_data = np.zeros_like(self.power_wheel_position)
        for ii, pos in enumerate(self.power_wheel_position):
            self.pw_target_position.update_value(pos)
            time.sleep(0.20)
            dose_calibration_data[ii] = self.collect_pm_power_data()
            time.sleep(0.20)
        return dose_calibration_data

    def calc_acq_times_array_const_dose_calibrated(self, t0, dose_calibration_data):
        '''predicts the acq times needed to have the same dose at every wheel position 
        based on calibration data'''
        dose = dose_calibration_data[0] * t0  # this the targeted dose.
        print('calc_acq_times_array_const_dose_calibrated() dose is:', dose)
        acq_times_array = np.array([round(item, 4)
                                    for item in dose / dose_calibration_data])
        return acq_times_array

    def calc_acq_times_array_const_dose_wheel_specs(self, t0, OD_MAX=4.3, OD_MAX_POS=270.):
        '''predicts the acq times needed to have the same dose at every wheel position 
        based on specification of the power wheel. Author: C. Kastel'''
        theta = self.power_wheel_position
        OD = OD_MAX * (theta - theta[0]) / OD_MAX_POS
        acq_times_array = np.array([round(item, 4)
                                    for item in (t0 * 10 ** (-OD))])
        print('Estimated time {}'.format(np.sum(acq_times_array)))
        return acq_times_array

    def calc_acq_times_array_manual_input(self, manual_pos_vs_times):
        pos, time = np.array(manual_pos_vs_times).T
        x = self.power_wheel_position
        # lowest position
        assert len(x) >= 2
        acq_times_array = np.piecewise(
            x, [x < pos[1], x >= pos[1]], [time[0], 0])
        # highest position
        acq_times_array += np.piecewise(x,
                                        [x >= pos[-1], x < pos[-1]], [time[-1], 0])
        # all other
        for i in range(1, len(pos) - 1):
            t = np.piecewise(x, [x < pos[i], x >= pos[i],
                                 x >= pos[i + 1]], [0, time[i], 0])
            acq_times_array += t
        return acq_times_array

    def optimize_at_opt_pw_pos(self):

        _measure = self.settings['opt_measure']
        measure = self.app.measurements[_measure]

        if self.settings['collect_andor_ccd']:
            ccdS = self.app.measurements['andor_ccd_readout'].settings
            if 'optimization_quantity' in measure.settings:
                measure.settings['optimization_quantity'] = 'measure/andor_ccd_readout/count_rate'
            ccdS['explore_mode_exposure_time'] = 0.1
            ccdS['explore_mode'] = True
            time.sleep(0.5)
            self.start_nested_measure_and_wait(measure, nested_interrupt=False)
            ccdS['explore_mode'] = False
            time.sleep(0.5)

        elif self.settings['collect_apd_counter']:
            t0 = self.apd_counter_hw.settings['int_time']
            self.app.measurements.apd_optimizer.settings['activation'] = False
            self.apd_counter_hw.settings['int_time'] = 0.1
            print(self.apd_count_rate_lq.val)
            self.app.measurements.apd_optimizer.settings['activation'] = True
            if 'optimization_quantity' in measure.settings:
                measure.settings['optimization_quantity'] = 'hardware/apd_counter/count_rate'
            time.sleep(0.1)
            self.start_nested_measure_and_wait(measure, nested_interrupt=False)
            self.apd_counter_hw.settings['int_time'] = t0
        else:
            self.start_nested_measure_and_wait(measure, nested_interrupt=False)

    def swap_reflector_and_collect_power(self, ii):
        reflector_pos = self.app.hardware['reflector_wheel'].settings.get_lq(
            'named_position')
        reflector_pos.update_value('mirror')
        # wait to swap detector
        time.sleep(self.settings['reflector_swap_duration'])

        ac = self.pm_hw.settings.average_count.val
        Ns = self.settings['power_meter_sample_number']
        t0 = time.time()
        self.pm_powers[ii] = self.collect_pm_power_data()

        reflector_pos.update_value('empty')
        # wait to swap detector
        time.sleep(self.settings['reflector_swap_duration'])

    def optimize_if_applicable(self, ii):
        S = self.settings
        if ii % S['opt_period'] == 0 and S['opt_period'] > 0:
            if S['opt_pw_pos'] != -1.0:
                p = S['opt_pw_pos']
            else:
                p = self.power_wheel_position[ii]
            self.pw_target_position.update_value(p)
            self.optimize_at_opt_pw_pos()

    def optimize_at_opt_pw_pos_(self):
        '''
        this function is invoked every S['opt_reriod']
        acquisition after the power is set to S['opt_pw_pos'].
        can be overwritten for more sophisticated procedures
        '''
        _measure = self.settings['opt_measure']
        measure = self.app.measurements[_measure]

        ccdS = self.app.measurements['andor_ccd_readout'].settings
        ccdHWS = self.app.hardware['andor_ccd'].settings
        ccdHWS['exposure_time'] = 0.1

        ccdS['continuous'] = True
        ccdS['activation'] = True
        acq_mode0 = ccdHWS['acq_mode']
        ccdHWS['acq_mode'] = 'single'
        T0 = ccdHWS['exposure_time']
        self.start_nested_measure_and_wait(measure, nested_interrupt=False)
        print(T0, 'setting exposure time')
        ccdS['continuous'] = False
        ccdS['activation'] = False
        time.sleep(0.1)
        ccdHWS['exposure_time'] = T0
        ccdHWS['acq_mode'] = acq_mode0
        time.sleep(0.1)
